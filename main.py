from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from models import Lap, Telemetry, engine, create_db_and_tables, get_session
from analytics import analyze_tyre_deg
from strategy import optimize_strategy, PIT_LOSS_MS
import pandas as pd
from typing import List

app = FastAPI(title="F1 Telemetry Analytics")

origins = [
    "http://98.92.249.217",
    "http://98.92.249.217:8000/",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health_check():
    return {"status": "online", "database": "connected"}

@app.get("/laps/{driver}", response_model=List[Lap])
def get_driver_laps(driver: str, session: Session = Depends(get_session)):
    statement = select(Lap).where(Lap.driver == driver.upper())
    results = session.exec(statement).all()
    if not results:
        raise HTTPException(status_code=404, detail="Driver data not found")
    return results

@app.get("/fastest-lap/{driver}")
async def get_driver_fastest_lap(driver: str, session: Session = Depends(get_session)):
    # SQLModel allows for a clean, Pythonic way to query your RDS MySQL
    statement = select(Lap).where(Lap.driver == driver).order_by(Lap.lap_time_ms)
    result = session.exec(statement).first()
    return result

@app.get("/telemetry/{lap_id}")
async def get_telemetry(lap_id: int, session: Session = Depends(get_session)):
    statement = select(Telemetry).where(Telemetry.lap_id == lap_id)
    results = session.exec(statement).all()
    return results

@app.get("/lap/drivers")
async def get_drivers(session: Session = Depends(get_session)):
    statement = select(Lap.driver).distinct().order_by(Lap.driver)
    return session.execute(statement).scalars().all()

@app.get("/lap/grand_prixs")
async def get_grand_prixs(session: Session = Depends(get_session)):
    statement = select(Lap.grand_prix).distinct().order_by(Lap.grand_prix)
    return session.execute(statement).scalars().all()

@app.get("/lap/years")
async def get_years(session: Session = Depends(get_session)):
    statement = select(Lap.year).distinct().order_by(Lap.year)
    return session.execute(statement).scalars().all()

@app.get("/analytics/degradation/{year}/{grand_prix}/{driver}")
def get_driver_degradation(year: int, grand_prix: str, driver: str, session: Session = Depends(get_session)):
    statement = select(Lap).where(
        Lap.year == year, 
        Lap.grand_prix == grand_prix, 
        Lap.driver == driver.upper()
    )
    results = session.exec(statement).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for this driver/race combo")

    df = pd.DataFrame([r.dict() for r in results])
    df['TotalLaps'] = df['lap_number'].max()
    df['LapTimeSeconds'] = df['lap_time_ms'] / 1000

    # 3. Run the Analytics Model
    deg_report = analyze_tyre_deg(df)

    # 4. Return as JSON
    return deg_report.to_dict(orient="records")

@app.get("/analytics/lap-chart", tags=["Analytics"])
def get_lap_chart_data(year: int, grand_prix: str, driver: str, session: Session = Depends(get_session)):
    statement = select(Lap).where(
        Lap.year == year, 
        Lap.grand_prix == grand_prix, 
        Lap.driver == driver.upper(),
        Lap.is_accurate == True
    ).order_by(Lap.lap_number)
    
    laps = session.exec(statement).all()
    
    if not laps:
        raise HTTPException(status_code=404, detail="No laps found")

    return [
        {
            "lap": lap.lap_number,
            "time": round(lap.lap_time_ms / 1000, 3),
            "compound": lap.compound,
            "stint": lap.stint
        }
        for lap in laps
    ]

@app.get("/analytics/strategy", tags=["Analytics"])
def get_pit_strategy(year: int, grand_prix: str, driver: str, session: Session = Depends(get_session)):
    statement = select(Lap).where(
        Lap.year == year,
        Lap.grand_prix == grand_prix,
        Lap.driver == driver.upper(),
    )
    laps = session.exec(statement).all()

    if not laps:
        raise HTTPException(status_code=404, detail="No data found for this driver/race combo")

    df = pd.DataFrame([r.dict() for r in laps])
    df['TotalLaps'] = df['lap_number'].max()
    df['LapTimeSeconds'] = df['lap_time_ms'] / 1000
    total_laps = int(df['lap_number'].max())

    deg_report = analyze_tyre_deg(df)

    if deg_report.empty:
        raise HTTPException(status_code=422, detail="Insufficient data: need 5+ accurate laps per stint")

    # Aggregate per compound: use freshest base pace, average degradation across stints
    compounds_data = {}
    for _, row in deg_report.iterrows():
        compound = row['compound']
        base_ms = float(row['intercept_pace']) * 1000
        deg_ms = float(row['deg_ms_per_lap'])
        if compound not in compounds_data:
            compounds_data[compound] = {'base_pace_ms': base_ms, 'deg_ms_per_lap': deg_ms, '_n': 1}
        else:
            cd = compounds_data[compound]
            cd['base_pace_ms'] = min(cd['base_pace_ms'], base_ms)
            cd['deg_ms_per_lap'] = (cd['deg_ms_per_lap'] * cd['_n'] + deg_ms) / (cd['_n'] + 1)
            cd['_n'] += 1
    for c in list(compounds_data):
        del compounds_data[c]['_n']

    # Build actual strategy from stints (accurate laps only)
    accurate = df[df['is_accurate'] == True].sort_values('lap_number')
    stint_groups = (
        accurate.groupby('stint', sort=True)
        .agg(compound=('compound', 'first'), start_lap=('lap_number', 'min'), end_lap=('lap_number', 'max'))
        .reset_index()
    )
    stint_groups['laps'] = stint_groups['end_lap'] - stint_groups['start_lap'] + 1
    actual_stints = [
        {
            'stint': int(row['stint']),
            'compound': str(row['compound']),
            'start_lap': int(row['start_lap']),
            'end_lap': int(row['end_lap']),
            'laps': int(row['laps']),
        }
        for _, row in stint_groups.iterrows()
    ]

    # Estimate actual strategy time using the same model (for fair comparison)
    actual_time_ms = 0.0
    for i, stint in enumerate(actual_stints):
        compound = stint['compound']
        if compound not in compounds_data:
            continue
        cd = compounds_data[compound]
        n = stint['laps']
        actual_time_ms += n * cd['base_pace_ms'] + max(0.0, cd['deg_ms_per_lap']) * n * (n - 1) / 2
        if i > 0:
            actual_time_ms += PIT_LOSS_MS

    actual_strategy = {
        'stints': actual_stints,
        'pit_stop_laps': [s['end_lap'] for s in actual_stints[:-1]],
        'num_pit_stops': len(actual_stints) - 1,
        'estimated_time_s': round(actual_time_ms / 1000, 1),
    }

    strategies = optimize_strategy(compounds_data, total_laps)

    for strat in strategies:
        strat['delta_s'] = round(strat['estimated_time_s'] - actual_strategy['estimated_time_s'], 1)

    return {
        'total_laps': total_laps,
        'pit_loss_s': 22,
        'actual_strategy': actual_strategy,
        'recommended_strategies': strategies,
        'compounds_analyzed': list(compounds_data.keys()),
    }
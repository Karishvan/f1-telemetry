from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from models import Lap, Telemetry, engine, create_db_and_tables, get_session
from analytics import analyze_tyre_deg
import pandas as pd
from typing import List

app = FastAPI(title="F1 Telemetry Analytics")

origins = [
    "http://98.92.249.217:5173/",
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

@app.get("/analytics/lap-chart/{year}/{grand_prix}/{driver}")
def get_lap_chart_data(year: int, grand_prix: str, driver: str, session: Session = Depends(get_session)):
    statement = select(Lap).where(
        Lap.year == year, 
        Lap.grand_prix == grand_prix, 
        Lap.driver == driver.upper(),
        Lap.is_accurate == 1
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
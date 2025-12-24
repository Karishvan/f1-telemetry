from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from models import Lap, Telemetry, engine, create_db_and_tables, get_session
from typing import List

app = FastAPI(title="F1 Telemetry Analytics")

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
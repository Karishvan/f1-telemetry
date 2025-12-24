from fastapi import FastAPI, Depends
from sqlmodel import Session, create_engine, select
from models import Lap, Telemetry
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the variables from .env into your system

DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)

app = FastAPI(title="F1 Telemetry API")

def get_session():
    with Session(engine) as session:
        yield session

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
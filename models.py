import os
from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL, echo=True)

class Lap(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int
    grand_prix: str
    driver: str
    lap_number: int
    lap_time_ms: float
    compound: str
    tyre_life: int
    stint: int
    is_accurate: bool

class Telemetry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lap_id: int = Field(foreign_key="lap.id")
    speed: int
    throttle: int
    gear: int

def create_db_and_tables():
    """Initializes the database schema in RDS"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for FastAPI endpoints to get a DB session"""
    with Session(engine) as session:
        yield session
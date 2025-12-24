from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session

class Lap(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int
    grand_prix: str
    driver: str
    lap_number: int
    lap_time_ms: float
    compound: str
    tyre_life: int

class Telemetry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lap_id: int = Field(foreign_key="lap.id")
    speed: int
    throttle: int
    gear: int
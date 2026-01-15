import gc
import time
import fastf1
import numpy as np
import pandas as pd
from sqlmodel import Session, select
from models import Lap, Telemetry, engine
from datetime import datetime

fastf1.Cache.enable_cache('f1_cache')

def backfill_season(year: int):
    schedule = fastf1.get_event_schedule(year)
    completed_races = schedule[schedule['EventDate'] < datetime.now()]

    for _, event in completed_races.iterrows():
        gp_name = event['EventName']
        
        with Session(engine) as session:
            if session.exec(select(Lap).where(Lap.grand_prix == gp_name, Lap.year == year)).first():
                continue

        print(f"Processing: {gp_name}...")
        try:
            f1_session = fastf1.get_session(year, gp_name, 'R')
            f1_session.load(telemetry=False, laps=True, weather=False) 

            for driver_num in f1_session.drivers:
                driver_info = f1_session.get_driver(driver_num)
                abb = driver_info['Abbreviation']
                
                process_driver_data(f1_session, abb, gp_name, year)
                
                gc.collect() 

            del f1_session
            gc.collect()
            print(f"Success: {gp_name}. Memory cleared.")
            
            # Small "breather" for the EC2 CPU/RAM to stabilize
            time.sleep(2)

        except Exception as e:
            print(f"Error in {gp_name}: {e}")

def process_driver_data(f1_session, abb, gp_name, year):
    """Processes a single driver and commits immediately to free RAM."""
    with Session(engine) as session:
        laps = f1_session.laps.pick_driver(abb)
        if laps.empty: return
        
        lap_objects = []
        
        for _, lap in laps.iterrows():
            
            if pd.isna(lap['LapTime']):
                continue

            new_lap = Lap(
                year=year, grand_prix=gp_name, driver=abb,
                lap_number=int(lap['LapNumber']),
                lap_time_ms=lap['LapTime'].total_seconds() * 1000,
                compound=lap['Compound'], tyre_life=int(lap['TyreLife']),
                stint = int(lap['Stint']),
                is_accurate=bool(lap['IsAccurate'])
            )
            lap_objects.append(new_lap)
        session.bulk_save_objects(lap_objects)
        session.commit()

if __name__ == "__main__":
    backfill_season(2024)
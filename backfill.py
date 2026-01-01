import fastf1
from sqlmodel import Session, select
from models import Lap, Telemetry, engine
from datetime import datetime

fastf1.Cache.enable_cache('f1_cache')

def backfill_season(year: int):
    schedule = fastf1.get_event_schedule(year)
    
    completed_races = schedule[schedule['EventDate'] < datetime.now()]
    
    print(f"Found {len(completed_races)} completed races for {year}.")

    for _, event in completed_races.iterrows():
        gp_name = event['EventName']
        
        with Session(engine) as session:
            # Check if we already have data for this GP
            statement = select(Lap).where(Lap.grand_prix == gp_name, Lap.year == year)
            exists = session.exec(statement).first()
            
            if exists:
                print(f"Skipping {gp_name} - already in database.")
                continue

            print(f"Ingesting: {gp_name}...")
            try:
                f1_session = fastf1.get_session(year, gp_name, 'R')
                f1_session.load()
                
                for driver_code in f1_session.drivers:
                    driver_info = f1_session.get_driver(driver_code)
                    driver_abb = driver_info['Abbreviation']
                    
                    laps = f1_session.laps.pick_driver(driver_abb)
                    if laps.empty: continue
                    
                    fastest_lap = laps.pick_fastest()
                    
                    
                    new_lap = Lap(
                        year=year,
                        grand_prix=gp_name,
                        driver=driver_abb,
                        lap_number=int(fastest_lap['LapNumber']),
                        lap_time_ms=fastest_lap['LapTime'].total_seconds() * 1000,
                        compound=fastest_lap['Compound'],
                        tyre_life=int(fastest_lap['TyreLife'])
                    )
                    session.add(new_lap)
                    session.commit()
                    session.refresh(new_lap)

                    
                    tel = fastest_lap.get_telemetry()
                    tel_list = [
                        Telemetry(
                            lap_id=new_lap.id,
                            speed=int(row['Speed']),
                            throttle=int(row['Throttle']),
                            gear=int(row['nGear'])
                        ) for _, row in tel.iterrows()
                    ]
                    session.bulk_save_objects(tel_list)
                    session.commit()
                
                print(f"Completed {gp_name}")
                
            except Exception as e:
                print(f"Error loading {gp_name}: {e}")

if __name__ == "__main__":
    backfill_season(2024)
import fastf1
from sqlmodel import Session, select
from models import Lap, Telemetry, engine
from datetime import datetime

# Enable caching to prevent redundant API calls
fastf1.Cache.enable_cache('f1_cache') 

def sync_latest_race():
    # Get the current year's schedule
    current_year = datetime.now().year
    schedule = fastf1.get_event_schedule(current_year)
    
    # Find the most recent completed race (EventNumber starts from 1)
    # We filter for events that have already happened
    past_events = schedule[schedule['EventDate'] < datetime.now()]
    if past_events.empty:
        print("No races have occurred yet this year.")
        return
        
    latest_event = past_events.iloc[-1]
    gp_name = latest_event['EventName']
    
    print(f"Checking data for: {gp_name} ({current_year})")

    with Session(engine) as session:
        # Check if this race already exists in our 'Lap' table
        statement = select(Lap).where(Lap.grand_prix == gp_name, Lap.year == current_year)
        existing_race = session.exec(statement).first()

        if existing_race:
            print(f"Data for {gp_name} already exists. Skipping ingestion.")
            return

        # If not found, load from FastF1
        print(f"New race detected! Loading {gp_name}...")
        f1_session = fastf1.get_session(current_year, gp_name, 'R')
        f1_session.load()

        driver_list = f1_session.drivers
        print(f"Processing all {len(driver_list)} drivers for {gp_name}...")

        for driver_num in driver_list:
            # Get driver details (Abbreviation, Team, etc.)
            driver_info = f1_session.get_driver(driver_num)
            driver_code = driver_info['Abbreviation']
            
            # Use a try-except block to handle drivers who DNF early or have no data
            try:
                driver_laps = f1_session.laps.pick_driver(driver_code)
                if driver_laps.empty:
                    continue
                
                fastest_lap = driver_laps.pick_fastest()

                # Create Lap object
                new_lap = Lap(
                    year=current_year,
                    grand_prix=gp_name,
                    driver=driver_code,
                    lap_number=int(fastest_lap['LapNumber']),
                    lap_time_ms=fastest_lap['LapTime'].total_seconds() * 1000,
                    compound=fastest_lap['Compound'],
                    tyre_life=int(fastest_lap['TyreLife'])
                )
                session.add(new_lap)
                session.commit()
                session.refresh(new_lap)

                # Save Telemetry
                telemetry = fastest_lap.get_telemetry()
                telemetry_objects = [
                    Telemetry(
                        lap_id=new_lap.id,
                        speed=int(row['Speed']),
                        stroke=int(row['Throttle']), # or other telemetry fields
                        gear=int(row['nGear'])
                    ) for _, row in telemetry.iterrows()
                ]
                session.bulk_save_objects(telemetry_objects)
                session.commit()
                
            except Exception as e:
                print(f"Could not process {driver_code}: {e}")

if __name__ == "__main__":
    sync_latest_race()
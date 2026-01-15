import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Standard F1 Constants for 2024/2025
FUEL_WEIGHT_PENALTY = 0.033  # seconds per kg (33ms)
AVG_FUEL_BURN_PER_LAP = 1.8   # kg per lap
TRACK_EVOLUTION_COEFFICIENT = 0.01

def get_corrected_time(lap_time_seconds, lap_number, total_laps):
    """
    Adjusts lap time to 'zero-fuel' equivalent. 
    Formula: Car is heaviest at Lap 1, lightest at Last Lap.
    """
    laps_remaining = total_laps - lap_number
    estimated_fuel_kg = laps_remaining * AVG_FUEL_BURN_PER_LAP
    
    # Subtract the penalty: lighter car = faster time
    # We "normalize" all laps to a 0kg fuel state to see pure tire performance
    fuel_correction = estimated_fuel_kg * FUEL_WEIGHT_PENALTY
    track_correction = lap_number * TRACK_EVOLUTION_COEFFICIENT

    fuel_adj = lap_time_seconds - fuel_correction

    return fuel_adj + track_correction

def analyze_tyre_deg(driver_laps_df):
    """
    Calculates deg rate (ms/lap) for each stint.
    driver_laps_df should contain: lap_number, LapTimeSeconds, stint, compound, TotalLaps
    """
    results = []
    
    # Group by stint to analyze each set of tires separately
    for stint_id, stint_data in driver_laps_df.groupby('stint'):
        # Filter: Remove outliers (Safety Cars, Pit Laps, mistakes > 107% pace)
        stint_data = stint_data[stint_data['is_accurate'] == True]
        if len(stint_data) < 5: continue
        
        # Apply Fuel Correction
        stint_data['CorrectedTime'] = stint_data.apply(
            lambda x: get_corrected_time(x['LapTimeSeconds'], x['lap_number'], x['TotalLaps']), 
            axis=1
        )
        
        # Linear Regression: X = Lap age in stint, Y = Corrected Lap Time
        # Age = current lap - first lap of stint
        X = (stint_data['lap_number'] - stint_data['lap_number'].min()).values.reshape(-1, 1)
        y = stint_data['CorrectedTime'].values
        
        model = LinearRegression().fit(X, y)
        deg_rate_sec = model.coef_[0] # slope: seconds lost per lap
        
        results.append({
            "stint": int(stint_id),
            "compound": stint_data['compound'].iloc[0],
            "deg_ms_per_lap": round(deg_rate_sec * 1000, 2),
            "intercept_pace": round(model.intercept_, 3) # "Base pace" on fresh tires
        })
        
    return pd.DataFrame(results)
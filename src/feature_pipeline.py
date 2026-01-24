import os
import requests
import hopsworks
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

def run_hourly():
    # 1. Connect to Hopsworks
    project = hopsworks.login(api_key_value=os.getenv('HOPSWORKS_TOKEN'))
    fs = project.get_feature_store()
    fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)

    # 2. Get Live Data for Karachi from OpenWeather
    LAT, LON = 24.8607, 67.0011
    API_KEY = os.getenv('OPENWEATHER_TOKEN')
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"
    
    response_raw = requests.get(url).json()
    response = response_raw['list'][0]
    new_ts = datetime.fromtimestamp(response['dt'])
    
    # 3. DUPLICATE CHECK: Ensure we don't upload the same hour twice
    # Pull only the last record to compare timestamps
    last_df = fg.read().sort_values(by="datetime").tail(1)
    last_ts = pd.to_datetime(last_df['datetime'].values[0])

    if new_ts <= last_ts:
        print(f"⏭️ Data for {new_ts} already exists in Hopsworks. Skipping...")
        return

    # 4. PREPARE ALL 17 FEATURES (Strictly matching the schema)
    # Note: We cast types explicitly to avoid 'bigint' vs 'int' errors
    new_data = {
        'datetime': [new_ts],
        'aqi': [int(response['main']['aqi'])],
        'co': [float(response['components']['co'])],
        'no2': [float(response['components']['no2'])],
        'o3': [float(response['components']['o3'])],
        'so2': [float(response['components']['so2'])],
        'pm2_5': [float(response['components']['pm2_5'])],
        'pm10': [float(response['components']['pm10'])],
        'nh3': [float(response['components']['nh3'])],
        'hour': [int(new_ts.hour)],
        'day_of_week': [int(new_ts.weekday())],
        'month': [int(new_ts.month)],
        # Lag features pulled from the last successful entry in Hopsworks
        'aqi_lag_1h': [float(last_df['aqi'].values[0])],
        'pm2_5_lag_1h': [float(last_df['pm2_5'].values[0])],
        'co_lag_1h': [float(last_df['co'].values[0])],
        'no2_lag_1h': [float(last_df['no2'].values[0])],
        'aqi_change_rate': [float(response['main']['aqi'] - last_df['aqi'].values[0])]
    }
    
    # 5. CREATE DATAFRAME AND FORCE TYPE CASTING
    new_df = pd.DataFrame(new_data)

    # Force Integer types to int32 (Standard 'int' in Hopsworks)
    int_cols = ['hour', 'day_of_week', 'month']
    for col in int_cols:
        new_df[col] = new_df[col].astype('int32')
        
    # Force Floating points to float64 (Standard 'double' in Hopsworks)
    float_cols = ['co', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3', 
                  'aqi_lag_1h', 'pm2_5_lag_1h', 'co_lag_1h', 'no2_lag_1h', 'aqi_change_rate']
    for col in float_cols:
        new_df[col] = new_df[col].astype('float64')

    # 6. INSERT TO HOPSWORKS
    fg.insert(new_df)
    print(f"✅ Successfully inserted new data for {new_ts} into 'karachi_aqi_fg'")

if __name__ == "__main__":
    run_hourly()
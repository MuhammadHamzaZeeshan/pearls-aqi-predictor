import os
import requests
import hopsworks
import pandas as pd
import time
from datetime import datetime
from dotenv import load_dotenv
from requests.exceptions import ConnectionError

# Load environment variables
load_dotenv()

def run_hourly():
    # 1. Connect to Hopsworks
    try:
        project = hopsworks.login(api_key_value=os.getenv('HOPSWORKS_TOKEN'))
        fs = project.get_feature_store()
        fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)
    except Exception as e:
        print(f"❌ Failed to login to Hopsworks: {e}")
        return

    # 2. Get Live Data for Karachi from OpenWeather
    LAT, LON = 24.8607, 67.0011
    API_KEY = os.getenv('OPENWEATHER_TOKEN')
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"
    
    try:
        response_raw = requests.get(url).json()
        response = response_raw['list'][0]
        new_ts = datetime.fromtimestamp(response['dt'])
    except Exception as e:
        print(f"❌ Failed to fetch data from OpenWeather: {e}")
        return
    
    # 3. DUPLICATE CHECK
    # Pull the last record to compare timestamps
    last_df = fg.read().sort_values(by="datetime").tail(1)
    
    if not last_df.empty:
        last_ts = pd.to_datetime(last_df['datetime'].values[0])
        if new_ts <= last_ts:
            print(f"⏭️ Data for {new_ts} already exists in Hopsworks. Skipping...")
            return
    else:
        print("ℹ️ Feature group is empty. Proceeding with first insertion.")

    # 4. PREPARE ALL 17 FEATURES
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
        'aqi_lag_1h': [float(last_df['aqi'].values[0]) if not last_df.empty else 0.0],
        'pm2_5_lag_1h': [float(last_df['pm2_5'].values[0]) if not last_df.empty else 0.0],
        'co_lag_1h': [float(last_df['co'].values[0]) if not last_df.empty else 0.0],
        'no2_lag_1h': [float(last_df['no2'].values[0]) if not last_df.empty else 0.0],
        'aqi_change_rate': [float(response['main']['aqi'] - last_df['aqi'].values[0]) if not last_df.empty else 0.0]
    }
    
    # 5. CREATE DATAFRAME AND FORCE TYPE CASTING
    new_df = pd.DataFrame(new_data)
    
    # Casting to ensure schema matching
    int_cols = ['hour', 'day_of_week', 'month']
    for col in int_cols:
        new_df[col] = new_df[col].astype('int32')
        
    float_cols = ['co', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3', 
                  'aqi_lag_1h', 'pm2_5_lag_1h', 'co_lag_1h', 'no2_lag_1h', 'aqi_change_rate']
    for col in float_cols:
        new_df[col] = new_df[col].astype('float64')

    # 6. INSERT TO HOPSWORKS WITH RETRY LOGIC (The Connection Fix)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🚀 Attempting to insert data (Attempt {attempt + 1}/{max_retries})...")
            fg.insert(new_df)
            print(f"✅ Successfully inserted new data for {new_ts}")
            break 
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30  # Wait 30s, then 60s
                print(f"⚠️ Connection error occurred: {e}")
                print(f"🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("❌ All retry attempts failed. Please check Hopsworks service status.")
                raise e

if __name__ == "__main__":
    run_hourly()
import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
TOKEN = os.getenv('OPENWEATHER_TOKEN')
LAT, LON = 24.8607, 67.0011  # Karachi

# 2. Define Time Range (Aug 1, 2025 to Jan 2, 2026)
# Note: OpenWeather uses Unix timestamps (seconds since 1970)
start_date = datetime(2025, 8, 1, 0, 0)
end_date = datetime(2026, 1, 23, 23, 59)

start_unix = int(start_date.timestamp())
end_unix = int(end_date.timestamp())

# 3. Construct API URL for History
url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={LAT}&lon={LON}&start={start_unix}&end={end_unix}&appid={TOKEN}"

print(f"⏳ Fetching history from {start_date} to {end_date}...")

# 4. Get the Data
response = requests.get(url)

if response.status_code == 200:
    raw_data = response.json()['list']
    
    # 5. Process into a Table
    data_rows = []
    for entry in raw_data:
        row = {
            "datetime": datetime.fromtimestamp(entry['dt']),
            "aqi": entry['main']['aqi'],
            "co": entry['components']['co'],
            "no2": entry['components']['no2'],
            "o3": entry['components']['o3'],
            "so2": entry['components']['so2'],
            "pm2_5": entry['components']['pm2_5'],
            "pm10": entry['components']['pm10'],
            "nh3": entry['components']['nh3']
        }
        data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    
    # 6. Save to Folder
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/karachi_aqi_history.csv', index=False)
    
    print(f"✅ Success! Saved {len(df)} hourly rows to data/karachi_aqi_history.csv")
else:
    print(f"❌ Failed: {response.status_code} - {response.text}")
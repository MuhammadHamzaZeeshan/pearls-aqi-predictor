# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()
# TOKEN = os.getenv('OPENWEATHER_TOKEN')

# # Karachi Coordinates
# lat, lon = 24.8607, 67.0011
# url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={TOKEN}"

# response = requests.get(url)
# data = response.json()

# if response.status_code == 200:
#     aqi = data['list'][0]['main']['aqi']
#     print(f"✅ OpenWeather Connection Successful!")
#     print(f"Karachi AQI (1-5 scale): {aqi}")
# else:
#     print(f"❌ Error {response.status_code}: {data.get('message', 'Unknown error')}")

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('OPENWEATHER_TOKEN')

# Karachi Coordinates
lat, lon = 24.8607, 67.0011
BASE_URL = "http://api.openweathermap.org/data/2.5"

# --------------------
# CURRENT AQI
# --------------------
current_url = f"{BASE_URL}/air_pollution?lat={lat}&lon={lon}&appid={TOKEN}"
current_response = requests.get(current_url)
current_data = current_response.json()

if current_response.status_code == 200:
    current_aqi = current_data['list'][0]['main']['aqi']
    print("✅ OpenWeather Connection Successful!")
    print(f"📍 Karachi Current AQI (1–5 scale): {current_aqi}")
else:
    print(f"❌ Error {current_response.status_code}: {current_data.get('message', 'Unknown error')}")
    exit()

# --------------------
# AQI FORECAST (Next 3 Days)
# --------------------
forecast_url = f"{BASE_URL}/air_pollution/forecast?lat={lat}&lon={lon}&appid={TOKEN}"
forecast_response = requests.get(forecast_url)
forecast_data = forecast_response.json()

if forecast_response.status_code != 200:
    print(f"❌ Forecast Error {forecast_response.status_code}: {forecast_data.get('message', 'Unknown error')}")
    exit()

daily_aqi = {}

for item in forecast_data["list"]:
    date = datetime.utcfromtimestamp(item["dt"]).date()
    aqi = item["main"]["aqi"]

    if date not in daily_aqi:
        daily_aqi[date] = []
    daily_aqi[date].append(aqi)

print("\n📅 AQI Forecast (Next 3 Days):")
for date, values in list(daily_aqi.items())[:4]:
    avg_aqi = round(sum(values) / len(values), 2)
    print(f"{date} → Avg AQI: {avg_aqi}")

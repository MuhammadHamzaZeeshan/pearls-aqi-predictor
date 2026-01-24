import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('OPENWEATHER_TOKEN')

# Karachi Coordinates
lat, lon = 24.8607, 67.0011
url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={TOKEN}"

response = requests.get(url)
data = response.json()

if response.status_code == 200:
    aqi = data['list'][0]['main']['aqi']
    print(f"✅ OpenWeather Connection Successful!")
    print(f"Karachi AQI (1-5 scale): {aqi}")
else:
    print(f"❌ Error {response.status_code}: {data.get('message', 'Unknown error')}")
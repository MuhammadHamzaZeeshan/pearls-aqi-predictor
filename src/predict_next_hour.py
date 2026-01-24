import os
import requests
import joblib
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('OPENWEATHER_TOKEN')
MODEL = joblib.load('models/karachi_aqi_model.joblib') # Load the saved brain

# Karachi Setup
LAT, LON = 24.8607, 67.0011

def get_live_forecast():
    # 1. Get CURRENT data to use as our "Lag"
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={TOKEN}"
    response = requests.get(url).json()
    
    current_aqi = response['list'][0]['main']['aqi']
    now = datetime.now()
    
    # 2. Prepare the data for the model (must match training features)
    input_data = pd.DataFrame([{
        'hour': (now.hour + 1) % 24, # Predict for NEXT hour
        'day_of_week': now.weekday(),
        'month': now.month,
        'aqi_lag_1h': current_aqi
    }])
    
    # 3. Predict
    prediction = MODEL.predict(input_data)[0]
    
    print(f"🕒 Current Time: {now.strftime('%H:%M')}")
    print(f"📡 Current Karachi AQI: {current_aqi}")
    print(f"🔮 Predicted AQI for {(now.hour + 1) % 24}:00 -> {prediction:.2f}")

if __name__ == "__main__":
    get_live_forecast()
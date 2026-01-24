import hopsworks
import joblib
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def run_inference():
    """
    Run inference and return forecast data along with model information.
    
    Returns:
        tuple: (forecast_df, model_info_dict)
    """
    # 1. Login and get model
    project = hopsworks.login(api_key_value=os.getenv('HOPSWORKS_TOKEN'))
    mr = project.get_model_registry()
    
    # Download the best model
    model_meta = mr.get_model("karachi_aqi_model", version=1)
    model_dir = model_meta.download()
    # Note: Depending on your model choice, it might be .joblib or .h5
    model_path = os.path.join(model_dir, "best_model.joblib")
    if not os.path.exists(model_path):
         model_path = os.path.join(model_dir, "best_model.h5")
    
    model = joblib.load(model_path)
    
    # Extract model name from the model object
    model_name = type(model).__name__
    model_info = {
        'model_name': model_name,
        'model_path': model_path,
        'model_type': 'Ensemble',
        'inference_time': datetime.now().isoformat()
    }
    
    # 2. Initialize Feature View to get correct column order
    fs = project.get_feature_store()
    feature_view = fs.get_feature_view(name="karachi_aqi_view", version=1)
    
    # 3. Get the latest record to start the forecast
    fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)
    df = fg.read().sort_values(by="datetime").tail(1)
    
    # Initial states from the last known real data
    current_aqi = df['aqi'].values[0]
    current_time = pd.to_datetime(df['datetime'].values[0])
    last_pm25 = df['pm2_5'].values[0]
    last_co = df['co'].values[0]
    last_no2 = df['no2'].values[0]
    
    forecast_data = []
    print(f"Generating 72-hour forecast starting from {current_time}...")

    # Get the exact list of string names the model expects
    # We remove 'datetime' and 'aqi' (the label)
    training_feature_names = [f.name for f in feature_view.query.features 
                             if f.name not in ['datetime', 'aqi']]

    for i in range(1, 73):
        next_time = current_time + timedelta(hours=i)
        
        # Build the input features
        input_data = {
            'co': [last_co], 'no2': [last_no2], 'o3': [df['o3'].values[0]], 
            'so2': [df['so2'].values[0]], 'pm2_5': [last_pm25], 'pm10': [df['pm10'].values[0]], 
            'nh3': [df['nh3'].values[0]],
            'hour': [next_time.hour],
            'day_of_week': [next_time.weekday()],
            'month': [next_time.month],
            'aqi_lag_1h': [current_aqi],
            'pm2_5_lag_1h': [last_pm25],
            'co_lag_1h': [last_co],
            'no2_lag_1h': [last_no2],
            'aqi_change_rate': [0] # Simplified for future forecasting
        }
        
        X = pd.DataFrame(input_data)
        
        # CRITICAL FIX: Reorder columns using the string names
        X = X[training_feature_names]
        
        prediction = model.predict(X)[0]
        
        forecast_data.append({
            'forecast_time': next_time,
            'predicted_aqi': round(float(prediction), 2)
        })
        
        # Recursive step: this prediction becomes the next hour's lag
        current_aqi = prediction

    # 4. Create forecast dataframe and optionally save
    forecast_df = pd.DataFrame(forecast_data)
    
    # Save to CSV for backup
    os.makedirs('data', exist_ok=True)
    forecast_df.to_csv('data/aqi_forecast_72h.csv', index=False)
    # Save model info to JSON for the dashboard to read
    model_info_path = os.path.join('data', 'model_info.json')
    try:
        with open(model_info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save model info JSON: {e}")

    print("72-hour forecast saved to data/aqi_forecast_72h.csv")
    print("Model info saved to data/model_info.json")
    
    return forecast_df, model_info

if __name__ == "__main__":
    forecast_df, model_info = run_inference()
    print(f"\nModel Info: {model_info}")
    print(f"Forecast Shape: {forecast_df.shape}")

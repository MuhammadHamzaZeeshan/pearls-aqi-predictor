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
    # 1. Login and get Model Registry
    project = hopsworks.login(api_key_value=os.getenv('HOPSWORKS_TOKEN'))
    mr = project.get_model_registry()
    
    # --- INDUSTRY THRESHOLD CHECK (REALISTIC ZONE) ---
    MAX_REALISTIC_R2 = 0.90  # Anything higher is rejected as overfitted
    MIN_ACCEPTABLE_R2 = 0.60  # Anything lower is rejected as underfitted
    
    print("🔎 Searching for a realistic, high-performing model...")
    all_models = mr.get_models("karachi_aqi_model")
    
    # Filter models based on your industry constraints
    realistic_models = [
        m for m in all_models 
        if MIN_ACCEPTABLE_R2 <= m.training_metrics.get('r2', 0) <= MAX_REALISTIC_R2
    ]

    if realistic_models:
        # Pick the one with the highest R2 within the Realistic Zone
        model_meta = max(realistic_models, key=lambda m: m.training_metrics.get('r2', 0))
        print(f"✅ Selected Realistic Model: Version {model_meta.version} (R2: {model_meta.training_metrics.get('r2'):.4f})")
    else:
        # Fallback: If no model is "realistic", we take the latest but print a heavy warning
        model_meta = mr.get_best_model("karachi_aqi_model", "r2", "max")
        print(f"⚠️ WARNING: No models found in the Realistic Zone ({MIN_ACCEPTABLE_R2}-{MAX_REALISTIC_R2}).")
        print(f"Falling back to Best Overall Model: Version {model_meta.version}")

    # 2. Download and Load Model
    model_dir = model_meta.download()
    model_path = os.path.join(model_dir, "best_model.joblib")
    if not os.path.exists(model_path):
         model_path = os.path.join(model_dir, "best_model.h5")
    
    model = joblib.load(model_path)
    
    model_info = {
        'model_name': type(model).__name__,
        'model_version': model_meta.version,
        'model_r2': model_meta.training_metrics.get('r2'),
        'inference_time': datetime.now().isoformat()
    }
    
    # 3. Setup Feature Store & View
    fs = project.get_feature_store()
    feature_view = fs.get_feature_view(name="karachi_aqi_view", version=1)
    fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)
    
    # Get latest data point for recursive start
    df = fg.read().sort_values(by="datetime").tail(1)
    
    current_aqi = df['aqi'].values[0]
    today = datetime.now().date()
    current_time = datetime.combine(today + timedelta(days=1), datetime.min.time())
    last_pm25 = df['pm2_5'].values[0]
    last_co = df['co'].values[0]
    last_no2 = df['no2'].values[0]
    
    # 4. Recursive Prediction Loop (72 Hours)
    forecast_data = []
    training_feature_names = [f.name for f in feature_view.query.features 
                             if f.name not in ['datetime', 'aqi']]

    for i in range(0, 72):
        next_time = current_time + timedelta(hours=i)
        
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
            'aqi_change_rate': [0]
        }
        
        X = pd.DataFrame(input_data)[training_feature_names]
        prediction = model.predict(X)[0]
        
        forecast_data.append({
            'forecast_time': next_time,
            'predicted_aqi': round(float(prediction), 2)
        })
        
        # Recursive update
        current_aqi = prediction

    # 5. Save Artifacts
    os.makedirs('data', exist_ok=True)
    pd.DataFrame(forecast_data).to_csv('data/aqi_forecast_72h.csv', index=False)
    
    with open(os.path.join('data', 'model_info.json'), 'w') as f:
        json.dump(model_info, f, indent=2)

    return pd.DataFrame(forecast_data), model_info

if __name__ == "__main__":
    run_inference()
import hopsworks
import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import tensorflow as tf

# Load environment variables
load_dotenv()

def run_inference():
    # 1. Login and get the Model Registry
    project = hopsworks.login(api_key_value=os.getenv('HOPSWORKS_TOKEN'))
    mr = project.get_model_registry()
    
    # --- REALISTIC ZONE FILTER ---
    # We reject models > 0.92 because they are likely overfitted/leaked
    MAX_REALISTIC_R2 = 0.92  
    MIN_ACCEPTABLE_R2 = 0.60  
    EVALUATION_METRIC = "r2"

    print("🔎 Searching for a realistic, high-performing model...")
    all_models = mr.get_models("karachi_aqi_model")
    
    # Filter for models that fall within our 'Defensible' zone
    realistic_models = [
        m for m in all_models 
        if MIN_ACCEPTABLE_R2 <= m.training_metrics.get(EVALUATION_METRIC, 0) <= MAX_REALISTIC_R2
    ]

    if realistic_models:
        # Pick the best one within the realistic range
        best_model_meta = max(realistic_models, key=lambda m: m.training_metrics.get(EVALUATION_METRIC, 0))
        print(f"🏆 Realistic Model Selected: Version {best_model_meta.version}")
        print(f"📊 {EVALUATION_METRIC.upper()} Score: {best_model_meta.training_metrics.get(EVALUATION_METRIC):.4f}")
    else:
        # Fallback if no model meets the criteria
        best_model_meta = all_models[0]
        print(f"⚠️ No model in Realistic Zone ({MIN_ACCEPTABLE_R2}-{MAX_REALISTIC_R2}). Using latest version: {best_model_meta.version}")

    # Download model files
    model_dir = best_model_meta.download()
    
    # 2. Flexible Model Loading
    model_path_joblib = os.path.join(model_dir, "best_model.joblib")
    model_path_h5 = os.path.join(model_dir, "best_model.h5")

    if os.path.exists(model_path_h5):
        print("🧠 Loading Neural Network model...")
        model = tf.keras.models.load_model(model_path_h5)
        is_nn = True
    else:
        print("🌲 Loading Random Forest/Ridge model...")
        model = joblib.load(model_path_joblib)
        is_nn = False
    
    # 3. Setup Feature Store and Feature View
    fs = project.get_feature_store()
    feature_view = fs.get_feature_view(name="karachi_aqi_view", version=1)
    fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)
    
    # Get the single latest record to kick off the recursive forecast
    df = fg.read().sort_values(by="datetime").tail(1)
    
    current_aqi = float(df['aqi'].values[0])
    current_time = pd.to_datetime(df['datetime'].values[0])
    last_pm25 = float(df['pm2_5'].values[0])
    last_co = float(df['co'].values[0])
    last_no2 = float(df['no2'].values[0])
    
    forecast_data = []
    print(f"🔮 Generating 72-hour forecast starting from {current_time}...")

    # Match the exact column order used during training
    training_feature_names = [f.name for f in feature_view.query.features 
                             if f.name not in ['datetime', 'aqi']]

    # 4. Recursive Prediction Loop
    for i in range(1, 73):
        next_time = current_time + timedelta(hours=i)
        
        input_data = {
            'co': [last_co], 'no2': [last_no2], 'o3': [df['o3'].values[0]], 
            'so2': [df['so2'].values[0]], 'pm2_5': [last_pm25], 'pm10': [df['pm10'].values[0]], 
            'nh3': [df['nh3'].values[0]],
            'hour': [int(next_time.hour)],
            'day_of_week': [int(next_time.weekday())],
            'month': [int(next_time.month)],
            'aqi_lag_1h': [float(current_aqi)],
            'pm2_5_lag_1h': [float(last_pm25)],
            'co_lag_1h': [float(last_co)],
            'no2_lag_1h': [float(last_no2)],
            'aqi_change_rate': [0.0] 
        }
        
        X = pd.DataFrame(input_data)
        X = X[training_feature_names] 
        
        # Predict
        prediction = model.predict(X)
        prediction_value = float(prediction[0][0]) if is_nn else float(prediction[0])
        
        forecast_data.append({
            'forecast_time': next_time,
            'predicted_aqi': round(prediction_value, 2)
        })
        
        # Recursive update
        current_aqi = prediction_value

    # 5. Save results
    forecast_df = pd.DataFrame(forecast_data)
    os.makedirs('data', exist_ok=True)
    forecast_df.to_csv('data/aqi_forecast_72h.csv', index=False)
    print("✅ 72-hour forecast successfully saved to data/aqi_forecast_72h.csv")

if __name__ == "__main__":
    run_inference()
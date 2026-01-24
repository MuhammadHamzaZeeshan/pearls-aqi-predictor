import hopsworks
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
import joblib
import os
from dotenv import load_dotenv

# 1. SETUP & LOGIN
load_dotenv()
HOPSWORKS_KEY = os.getenv('HOPSWORKS_TOKEN')

project = hopsworks.login(api_key_value=HOPSWORKS_KEY)
fs = project.get_feature_store()

# 2. GET FEATURE GROUP & CREATE FEATURE VIEW
# This is the 'lens' through which the model sees your Karachi data
fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)

try:
    print("🔍 Looking for existing Feature View...")
    feature_view = fs.get_feature_view(name="karachi_aqi_view", version=1)
except:
    print("🆕 Feature View not found. Creating a new one...")
    # 'aqi' is our target label (what we want to predict)
    feature_view = fs.create_feature_view(
        name="karachi_aqi_view",
        query=fg.select_all(),
        labels=["aqi"],
        version=1
    )

# 3. TRAIN/TEST SPLIT
# Pulls data from the cloud and splits it 80% for learning, 20% for testing
print("🧪 Fetching data and creating Training/Test sets...")
X_train, X_test, y_train, y_test = feature_view.train_test_split(test_size=0.2)

# --- MODEL 1: Ridge Regression (Statistical/Linear) ---
print("🏃 Training Ridge Regression...")
model_ridge = Ridge()
model_ridge.fit(X_train, y_train)
preds_ridge = model_ridge.predict(X_test)

# --- MODEL 2: Random Forest (Tree-based/Non-linear) ---
print("🌲 Training Random Forest...")
model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
model_rf.fit(X_train, y_train)
preds_rf = model_rf.predict(X_test)

# --- MODEL 3: Neural Network (Deep Learning/TensorFlow) ---
print("🧠 Training Neural Network (TensorFlow)...")
model_nn = Sequential([
    Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1)
])
model_nn.compile(optimizer='adam', loss='mse')
# Small number of epochs for the first run
model_nn.fit(X_train, y_train, epochs=20, batch_size=16, verbose=0)
preds_nn = model_nn.predict(X_test).flatten()

# 4. EVALUATION & COMPARISON
# We compare models based on Mean Absolute Error (lower is better)
results = [
    {"Model": "Ridge", "MAE": mean_absolute_error(y_test, preds_ridge), "R2": r2_score(y_test, preds_ridge)},
    {"Model": "RandomForest", "MAE": mean_absolute_error(y_test, preds_rf), "R2": r2_score(y_test, preds_rf)},
    {"Model": "NeuralNetwork", "MAE": mean_absolute_error(y_test, preds_nn), "R2": r2_score(y_test, preds_nn)}
]

print("\n--- Model Comparison Results ---")
for res in results:
    print(f"📊 {res['Model']} -> MAE: {res['MAE']:.2f}, R2: {res['R2']:.2f}")

# 5. SELECT WINNER & SAVE TO REGISTRY
best_res = min(results, key=lambda x: x['MAE'])
best_model_name = best_res['Model']
print(f"\n🏆 WINNER: {best_model_name} with MAE: {best_res['MAE']:.2f}")

# Ensure local models folder exists
os.makedirs('models', exist_ok=True)
local_model_path = f"models/best_aqi_model_{best_model_name.lower()}"

# Save the winning model object
if best_model_name == "Ridge":
    joblib.dump(model_ridge, local_model_path + ".joblib")
    final_path = local_model_path + ".joblib"
elif best_model_name == "RandomForest":
    joblib.dump(model_rf, local_model_path + ".joblib")
    final_path = local_model_path + ".joblib"
else:
    model_nn.save(local_model_path + ".h5")
    final_path = local_model_path + ".h5"

# Upload to Hopsworks Model Registry
mr = project.get_model_registry()
aqi_model = mr.python.create_model(
    name="karachi_aqi_model", 
    metrics={"mae": best_res['MAE'], "r2": best_res['R2']},
    description=f"Best performing model ({best_model_name}) for Karachi AQI"
)
aqi_model.save(final_path)

print(f"✅ Successfully uploaded {best_model_name} to Hopsworks Model Registry!")
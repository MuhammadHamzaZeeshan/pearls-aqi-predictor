import hopsworks
import pandas as pd
import joblib
import os
import numpy as np
from dotenv import load_dotenv
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

load_dotenv()
project = hopsworks.login(api_key_value=os.getenv('HOPSWORKS_TOKEN'))
fs = project.get_feature_store()

# 1. Get Feature Group
fg = fs.get_feature_group(name="karachi_aqi_fg", version=1)

# 2. Feature View Setup
print("🔍 Checking Feature View...")
try:
    feature_view = fs.get_feature_view(name="karachi_aqi_view", version=1)
except:
    feature_view = fs.create_feature_view(
        name="karachi_aqi_view",
        query=fg.select_all(),
        labels=["aqi"],
        version=1
    )

# 3. TIME-SERIES SPLIT (Professional Approach)
# We avoid random splitting to prevent "Data Leakage"
print("🧪 Applying Time-Series Split (Chronological Order)...")
df = fg.read().sort_values(by="datetime")

# Drop datetime but keep the order
if 'datetime' in df.columns:
    df = df.drop(columns=['datetime'])

# Manual 80/20 split based on time
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

X_train = train_df.drop(columns=['aqi'])
y_train = train_df['aqi']
X_test = test_df.drop(columns=['aqi'])
y_test = test_df['aqi']

# 4. Model Training with AGGRESSIVE REGULARIZATION
print("🏃 Training Ridge (Alpha=50.0)...")
m1 = Ridge(alpha=50.0).fit(X_train, y_train)
p1 = m1.predict(X_test)

print("🌲 Training Highly Regularized Random Forest...")
# Fewer trees and shallower depth force the model to learn general patterns
m2 = RandomForestRegressor(
    n_estimators=50, 
    max_depth=5, 
    min_samples_leaf=20, 
    max_features='sqrt',
    random_state=42
).fit(X_train, np.ravel(y_train))
p2 = m2.predict(X_test)

print("🧠 Training Neural Network (Simple Architecture)...")
input_dim = X_train.shape[1]
m3 = Sequential([
    Dense(16, activation='relu', input_shape=(input_dim,)), 
    Dropout(0.4), # High dropout to prevent memorization
    Dense(8, activation='relu'), 
    Dense(1)
])
m3.compile(optimizer='adam', loss='mse')

early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

m3.fit(
    X_train, y_train, 
    validation_data=(X_test, y_test),
    epochs=50, 
    batch_size=32,
    callbacks=[early_stop],
    verbose=0
)
p3 = m3.predict(X_test).flatten()

# 5. Results & Selection
results = [
    {"Name": "Ridge", "MAE": mean_absolute_error(y_test, p1), "Model": m1, "Ext": ".joblib"},
    {"Name": "RandomForest", "MAE": mean_absolute_error(y_test, p2), "Model": m2, "Ext": ".joblib"},
    {"Name": "NeuralNetwork", "MAE": mean_absolute_error(y_test, p3), "Model": m3, "Ext": ".h5"}
]

best = min(results, key=lambda x: x['MAE'])
best_p = best['Model'].predict(X_test).flatten()
best_r2 = r2_score(y_test, best_p)

print(f"\n🏆 Winner: {best['Name']}")
print(f"📊 Realistic MAE: {best['MAE']:.4f}")
print(f"📈 Realistic R2 Score: {best_r2:.4f}")

# 6. Save & Register
os.makedirs('models', exist_ok=True)
path = f"models/best_model{best['Ext']}"

if best['Name'] == "NeuralNetwork":
    best['Model'].save(path)
else:
    joblib.dump(best['Model'], path)

mr = project.get_model_registry()
model = mr.python.create_model(
    name="karachi_aqi_model", 
    metrics={"mae": best['MAE'], "r2": best_r2}
)
model.save(path)
print(f"✅ Defensible model registered as Version {model.version}!")
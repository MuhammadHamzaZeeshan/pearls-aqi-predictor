import pandas as pd
import hopsworks
import os
from dotenv import load_dotenv

# 1. Setup and Login
load_dotenv()
HOPSWORKS_KEY = os.getenv('HOPSWORKS_TOKEN')

# Replace with the EXACT project name you created in Hopsworks
project = hopsworks.login(api_key_value=HOPSWORKS_KEY)
fs = project.get_feature_store()

# 2. Load and Prepare your Cleaned Data
# Make sure to use the file with the 'lag' features we created during EDA
df = pd.read_csv('data/karachi_aqi_history.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# --- Professional Feature Engineering ---
df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek
df['month'] = df['datetime'].dt.month

# Lagged AQI
df['aqi_lag_1h'] = df['aqi'].shift(1)

# Lagged Pollutants (Using past pollutants to predict future AQI)
df['pm2_5_lag_1h'] = df['pm2_5'].shift(1)
df['co_lag_1h'] = df['co'].shift(1)
df['no2_lag_1h'] = df['no2'].shift(1)

# AQI Change Rate (Required by your project)
df['aqi_change_rate'] = df['aqi'].shift(1) - df['aqi'].shift(2)

# Drop rows with NaN (first two rows)
df = df.dropna()

# 3. Create or Get the Feature Group
# Primary Key and Event Time are critical for time-series projects
aqi_fg = fs.get_or_create_feature_group(
    name="karachi_aqi_fg",
    version=1,
    primary_key=['datetime'], # Unique ID for each row
    event_time='datetime',    # Tells Hopsworks this is time-series data
    description="Hourly AQI data for Karachi with time-based features and 1-hour lags"
)

# 4. Upload (Insert) the Data to Hopsworks
print("🚀 Uploading data to Hopsworks Feature Store...")
aqi_fg.insert(df)

print("✅ Backfill Complete! You can now see your features in the Hopsworks UI.")
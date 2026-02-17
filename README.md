# Pearls: Karachi AQI Predictor

A serverless MLOps system for predicting Air Quality Index (AQI) trends in Karachi, Pakistan.

---

## Overview

This project was developed during the 10Pearls Data Science Internship. It implements a complete end-to-end MLOps lifecycle to predict Air Quality Index (AQI) for the Karachi Metropolitan area.

The system fetches live pollution data from OpenWeather API, stores features in Hopsworks Feature Store, trains machine learning models, and generates 72-hour AQI forecasts.

---

## Key Features

- Real-time data ingestion from OpenWeather API (hourly updates)
- Serverless automation using GitHub Actions
- Feature storage and versioning with Hopsworks
- Automatic model selection based on MAE and R2 thresholds
- 72-hour recursive forecasting
- Interactive Streamlit dashboard for visualization

---

## Live Dashboard

The interactive AQI prediction dashboard is deployed and accessible online:

**[https://pearls-aqi-predictor-hamza.streamlit.app/](https://pearls-aqi-predictor-hamza.streamlit.app/)**

View real-time 72-hour AQI forecasts for Karachi, historical trends, and model performance metrics.

---

## Project Structure

```
pearls-aqi-predictor/
|
|-- .github/
|   |-- workflows/
|       |-- hourly_feature_pipeline.yml    # Fetches new data every hour
|       |-- daily_training_pipeline.yml    # Retrains models daily at midnight
|       |-- daily_inference_pipeline.yml   # Generates 72h forecast daily
|
|-- app/
|   |-- main.py                            # Streamlit dashboard application
|   |-- requirements.txt                   # Dashboard dependencies
|
|-- data/
|   |-- aqi_forecast_72h.csv               # Latest 72-hour predictions
|   |-- karachi_aqi_history.csv            # Historical AQI data (Aug 2025 - Jan 2026)
|   |-- model_info.json                    # Model metrics and selection info
|
|-- Images/                                # Project images and visuals
|
|-- models/
|   |-- best_model.joblib                  # Saved best performing model
|   |-- karachi_aqi_model.joblib           # Local model copy
|
|-- notebooks/
|   |-- 01_Initial_EDA.ipynb               # Exploratory data analysis notebook
|
|-- src/
|   |-- backfill_data.py                   # Fetches historical data from OpenWeather
|   |-- feature_pipeline.py                # Hourly data fetch and feature engineering
|   |-- hopsworks_backfill.py              # Uploads historical data to Hopsworks
|   |-- inference_pipeline.py              # Generates 72-hour forecasts
|   |-- predict_next_hour.py               # Single hour prediction script
|   |-- test_api.py                        # API connection test script
|   |-- training_pipeline.py               # Model training and evaluation
|
|-- karachi_daily_aqi_weather.csv          # Additional weather data
|-- requirements.txt                       # Project dependencies
|-- README.md                              # This file
```

---

## Workflow

The system operates on three automated pipelines:

### 1. Feature Pipeline (Runs Hourly)

- Fetches current AQI and pollutant data from OpenWeather API
- Extracts pollutants: PM2.5, PM10, CO, NO2, O3, SO2, NH3
- Engineers features: time features (hour, day_of_week, month), lag features (aqi_lag_1h, pm2_5_lag_1h, co_lag_1h, no2_lag_1h), and change rate
- Inserts new data into Hopsworks Feature Store

### 2. Training Pipeline (Runs Daily)

- Reads all data from the Feature Store
- Applies time-series split (80% train, 20% test) to prevent data leakage
- Trains three models:
  - Ridge Regression (alpha=50.0)
  - Random Forest (max_depth=5, n_estimators=50)
  - Neural Network (16-8-1 architecture with dropout)
- Selects the model with lowest MAE
- Registers the best model in Hopsworks Model Registry

### 3. Inference Pipeline (Runs Daily)

- Downloads the best model from Model Registry
- Validates model R2 score
- Generates 72-hour recursive forecast
- Saves predictions to `data/aqi_forecast_72h.csv`

---

## Features Used

The model uses 17 features for prediction:

- **Pollutants**: co, no2, o3, so2, pm2_5, pm10, nh3, aqi
- **Time Features**: datetime, hour, day_of_week, month
- **Lag Features**: aqi_lag_1h, pm2_5_lag_1h, co_lag_1h, no2_lag_1h
- **Change Features**: aqi_change_rate

---

## How to Run

### Prerequisites

- Python 3.11
- OpenWeather API key (for air pollution data)
- Hopsworks account and API token

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/MuhammadHamzaZeeshan/pearls-aqi-predictor.git
   cd pearls-aqi-predictor
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory:
   ```
   HOPSWORKS_TOKEN=your_hopsworks_api_key
   OPENWEATHER_TOKEN=your_openweather_api_key
   ```

### Running the Pipelines Locally

**Fetch new data (Feature Pipeline):**
```
python src/feature_pipeline.py
```

**Train models (Training Pipeline):**
```
python src/training_pipeline.py
```

**Generate forecast (Inference Pipeline):**
```
python src/inference_pipeline.py
```

### Running the Dashboard

```
cd app
pip install -r requirements.txt
streamlit run main.py
```

The dashboard will open in your browser showing:
- Current AQI status
- 72-hour forecast chart
- Model comparison metrics
- Historical pollutant trends

---

## Data Sources

- **AQI and Pollutant Data**: OpenWeather Air Pollution API
- **Location**: Karachi, Pakistan (Lat: 24.8607, Lon: 67.0011)
- **Historical Range**: August 2025 to present
- **Update Frequency**: Hourly

---

## GitHub Actions Automation

The repository includes three GitHub Actions workflows that run automatically:

- `hourly_feature_pipeline.yml` - Runs every hour at minute 0
- `daily_training_pipeline.yml` - Runs daily at midnight UTC
- `daily_inference_pipeline.yml` - Runs daily at midnight UTC

To enable automation, add the following secrets to your GitHub repository:
- `HOPSWORKS_TOKEN`
- `OPENWEATHER_TOKEN`

---

## Technologies Used

- **Machine Learning**: scikit-learn, TensorFlow/Keras
- **Feature Store**: Hopsworks
- **Data Processing**: pandas, numpy
- **Visualization**: Streamlit, Plotly
- **Automation**: GitHub Actions
- **Model Serialization**: joblib

---

## License

This project was developed as part of the 10Pearls Data Science Internship program.
# Pearls: Karachi AQI Predictor
**A serverless MLOps engine for real-time air quality forecasting.**

---

### Overview
This project was developed during the **10Pearls Data Science Internship (January 2026)**. It implements a complete end-to-end MLOps lifecycle to predict Air Quality Index (AQI) trends for the Karachi Metropolitan area. 

The system utilizes a **Serverless Architecture** to ingest live data, update features, and serve 72-hour forecasts with a verified **0.87 R² Score**, ensuring the model captures true atmospheric trends rather than just overfitted noise.



---

### Key Features
* **Real-Time Data Ingestion:** Automated hourly pollutants (PM2.5, CO, NO2) and weather fetching from OpenWeather API.
* **Serverless MLOps:** Uses GitHub Actions to orchestrate the feature, training, and inference pipelines.
* **Metric-Based Model Selection:** Automatically deploys the "Best Model" from the Hopsworks Model Registry based on R² and MAE thresholds.
* **Recursive Forecasting:** Implements a time-series recursive loop to generate high-resolution 72-hour future trends.
* **Sober Dashboard:** A professional, minimalist Streamlit interface designed for high-contrast readability.

---

### Technical Architecture
The project is structured into three distinct heartbeats:

1.  **Feature Pipeline (Hourly):** Ingests raw data and performs engineering (lags, change rates) into the Hopsworks Feature Store.
2.  **Inference Pipeline (Hourly):** Fetches the latest "Realistic" model and generates a new `72h_forecast.csv`.
3.  **Training Pipeline (Daily):** Retrains the Random Forest and Neural Network models on the accumulated daily data to prevent model staleness.

---

### Project Structure
```text
pearls-aqi-predictor/
├── .github/workflows/    # CI/CD pipelines (Automation)
├── app/                  # Streamlit Dashboard (UI)
├── data/                 # Local data caches for fast serving
├── src/                  # Core Logic (Feature, Training, Inference)
├── requirements.txt      # Project dependencies
└── .env                  # Environment secrets (API Tokens)
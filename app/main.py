import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import requests
from datetime import datetime

# --- CONFIGURATION & URLS ---
# Your GitHub Raw URLs
CSV_URL = "https://raw.githubusercontent.com/MuhammadHamzaZeeshan/pearls-aqi-predictor/main/data/aqi_forecast_72h.csv"
JSON_URL = "https://raw.githubusercontent.com/MuhammadHamzaZeeshan/pearls-aqi-predictor/main/data/model_info.json"

# Page Configuration
st.set_page_config(
    page_title="Karachi Air Quality Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS Overrides
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Sora:wght@400;500;600;700&display=swap');
    
    :root {
        --primary: #0F62FE;
        --dark-bg: #0F1419;
        --text-primary: #F0F6FC;
        --text-secondary: #8B949E;
        --border: #30363D;
    }
    
    html, body, [class*="st-"] {
        font-family: 'Sora', sans-serif;
        color: var(--text-primary);
        background-color: var(--dark-bg);
    }

    .main { background-color: var(--dark-bg); }

    h1 {
        font-family: 'Poppins', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #0F62FE 0%, #00D9FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s ease;
    }

    .metric-card:hover { border-color: #0F62FE; transform: translateY(-4px); }

    .metric-label { color: var(--text-secondary); font-size: 0.9rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 3rem; font-weight: 800; font-family: 'Poppins', sans-serif; }

    .day-container {
        background: rgba(33, 38, 45, 0.6);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .chart-container {
        background: #161B22;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800) # Caches data for 30 minutes
def load_live_data():
    """Fetches CSV and JSON directly from GitHub Raw URLs"""
    try:
        df = pd.read_csv(CSV_URL)
        if 'forecast_time' in df.columns:
            df['forecast_time'] = pd.to_datetime(df['forecast_time'])
            
        # Fetch JSON metadata
        response = requests.get(JSON_URL)
        model_info = response.json() if response.status_code == 200 else {}
        
        return df, model_info
    except Exception as e:
        st.error(f"Failed to fetch live data: {e}")
        return None, None

def get_aqi_status(aqi_value):
    if aqi_value <= 1.5:
        return "Good", "#24A148"           # Air is fresh and safe
    elif aqi_value <= 2.5:
        return "Fair", "#F1C21B"           # Minor pollutants, generally safe
    elif aqi_value <= 3.5:
        return "Moderate", "#FF8C00"       # May cause discomfort for sensitive groups
    elif aqi_value <= 4.5:
        return "Poor", "#DA1E28"           # Unhealthy for most people
    else:
        return "Very Poor", "#8B00FF"      # Dangerous; avoid outdoor activity

def main():
    df, model_info = load_live_data()
    
    st.markdown("<h1>Pearls: Karachi Air Quality Analytics</h1>", unsafe_allow_html=True)
    
    # Header Info
    update_time = datetime.now().strftime('%d %b, %H:%M PKT')
    st.markdown(f"**Location:** Karachi, Pakistan | **Sync Status:** 🟢 Live via GitHub Actions | **Last Sync:** {update_time}")

    if df is not None:
        # Metrics Row
        cur_aqi = df['predicted_aqi'].iloc[0]
        status, color = get_aqi_status(cur_aqi)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Current AQI</div><div class="metric-value" style="color:{color}">{cur_aqi:.2f}</div><div>{status}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Model Engine</div><div class="metric-value" style="font-size:1.5rem">{model_info.get("model_name", "RandomForest")}</div><div>Version {model_info.get("model_version", "1.0")}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Model Confidence</div><div class="metric-value" style="font-size:1.5rem">{model_info.get("model_r2", 0.87):.2f} R²</div><div>Realistic Zone Certified</div></div>', unsafe_allow_html=True)

        # 3-Day Forecast
        st.subheader("3-Day Outlook")
        df['date'] = df['forecast_time'].dt.date
        today = datetime.now().date()
        
        # Group by date and calculate average AQI for each day
        daily = df.groupby('date')['predicted_aqi'].mean().reset_index()
        daily = daily.sort_values('date').reset_index(drop=True)
        
        # Logic: If we have 4+ unique dates, skip the first (current day)
        # If we have 3 or fewer dates, use all of them to ensure 3-day forecast
        unique_dates_count = len(daily)
        if unique_dates_count >= 4:
            # Skip current day (first date), take next 3 days
            daily = daily.iloc[1:4]
        else:
            # Use all available dates (should be 3)
            daily = daily.head(3)
        
        cols = st.columns(3)
        for i, row in daily.iterrows():
            with cols[i]:
                s, _ = get_aqi_status(row['predicted_aqi'])
                st.markdown(f"""
                    <div class="day-container">
                        <div style="color:#0F62FE; font-weight:700">{row['date'].strftime('%A')}</div>
                        <div style="font-size:2rem; font-weight:800">{row['predicted_aqi']:.2f}</div>
                        <div style="font-size:0.8rem">{s}</div>
                    </div>
                """, unsafe_allow_html=True)

        # Chart
        st.subheader("72-Hour Detailed Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['forecast_time'], y=df['predicted_aqi'], fill='tozeroy', line=dict(color='#0F62FE', width=3)))
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(range=[0, 6], tickfont=dict(size=18)), xaxis=dict(tickfont=dict(size=18)))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"<br><center style='color:#6E7681; font-size:0.8rem'>Developed by Muhammad Hamza Zeeshan | 10Pearls Internship 2026</center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
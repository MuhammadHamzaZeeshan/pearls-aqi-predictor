import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Karachi Air Quality Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS Overrides - Industry Standard Design
st.markdown("""
    <style>
    /* Typography & Color System */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Sora:wght@400;500;600;700&display=swap');
    
    :root {
        --primary: #0F62FE;
        --primary-light: #0043CE;
        --success: #24A148;
        --warning: #F1C21B;
        --alert: #DA1E28;
        --dark-bg: #0F1419;
        --secondary-bg: #161B22;
        --tertiary-bg: #21262D;
        --border: #30363D;
        --text-primary: #F0F6FC;
        --text-secondary: #8B949E;
        --text-tertiary: #6E7681;
    }
    
    html, body, [class*="st-"] {
        font-family: 'Sora', sans-serif;
        color: var(--text-primary);
        background-color: var(--dark-bg);
        font-size: 16px;
        line-height: 1.6;
    }
    
    .main {
        background: linear-gradient(135deg, #0F1419 0%, #161B22 100%);
        color: var(--text-primary);
    }
    
    /* Typography Hierarchy */
    h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        color: var(--text-primary);
        margin: 0;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #0F62FE 0%, #00D9FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        font-family: 'Poppins', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }
    
    h3 {
        font-family: 'Poppins', sans-serif;
        font-size: 1.6rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    
    /* Metric Cards - Premium Style */
    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 28px 24px;
        text-align: left;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #0F62FE, #00D9FF);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: #0F62FE;
        box-shadow: 0 8px 24px rgba(15, 98, 254, 0.15);
        transform: translateY(-4px);
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.95rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
        font-family: 'Poppins', sans-serif;
    }
    
    .metric-value {
        color: var(--text-primary);
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #F0F6FC 0%, #A8D5FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-subtext {
        color: var(--text-tertiary);
        font-size: 1rem;
        margin-top: 8px;
    }
    
    /* Daily Forecast Cards */
    .day-container {
        background: linear-gradient(135deg, rgba(33, 38, 45, 0.6) 0%, rgba(22, 27, 34, 0.8) 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .day-container:hover {
        border-color: #0F62FE;
        background: linear-gradient(135deg, rgba(15, 98, 254, 0.1) 0%, rgba(0, 217, 255, 0.05) 100%);
        transform: translateY(-6px);
        box-shadow: 0 12px 32px rgba(15, 98, 254, 0.2);
    }
    
    .day-name {
        color: #0F62FE;
        font-weight: 700;
        font-size: 1.05rem;
        font-family: 'Poppins', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    
    .day-date {
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin-bottom: 16px;
        font-weight: 500;
    }
    
    .day-aqi {
        color: var(--text-primary);
        font-size: 2.6rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        line-height: 1.1;
    }
    
    .day-status {
        font-size: 0.9rem;
        margin-top: 8px;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        font-weight: 600;
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border);
    }
    
    .section-header h3 {
        margin: 0;
    }
    
    .section-icon {
        font-size: 1.5rem;
        margin-right: 12px;
    }
    
    /* Station Info */
    .station-info {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 2rem;
        color: var(--text-secondary);
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .station-info-icon {
        font-size: 1.2rem;
    }
    
    /* Footer Styling */
    .footer-text {
        color: var(--text-tertiary);
        font-size: 0.85rem;
        text-align: center;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border);
    }
    
    /* Chart Container */
    .chart-container {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        margin: 1.5rem 0;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        h1 { font-size: 2.4rem; }
        .metric-value { font-size: 2.6rem; }
        .day-aqi { font-size: 2rem; }
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    """
    Load forecast data and model info from files saved by the inference pipeline.
    Returns: (forecast_df, model_info_dict) or (None, None) if data unavailable
    """
    csv_path = "data/aqi_forecast_72h.csv"
    model_info_path = "data/model_info.json"

    if not os.path.exists(csv_path):
        return None, None

    df = pd.read_csv(csv_path)
    if 'forecast_time' in df.columns:
        df['forecast_time'] = pd.to_datetime(df['forecast_time'])

    model_info = None
    if os.path.exists(model_info_path):
        try:
            with open(model_info_path, 'r', encoding='utf-8') as f:
                model_info = json.load(f)
        except Exception:
            model_info = None

    # Fallback model info if JSON missing
    if model_info is None:
        model_info = {
            'model_name': 'Unknown',
            'model_type': 'N/A',
            'inference_time': 'N/A',
            'source': 'cached'
        }

    return df, model_info

def get_aqi_status(aqi_value):
    """Determine AQI status badge color and label"""
    if aqi_value <= 50:
        return "Good", "#24A148"
    elif aqi_value <= 100:
        return "Moderate", "#F1C21B"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive", "#FF8C00"
    elif aqi_value <= 200:
        return "Unhealthy", "#DA1E28"
    else:
        return "Very Unhealthy", "#8B00FF"

def main():
    df, model_info = load_data()
    
    # 1. Header Section with Professional Typography
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1>Air Quality Analytics</h1>", unsafe_allow_html=True)
    
    # Station Info Card
    current_time = datetime.now().strftime('%H:%M PKT')
    st.markdown(f"""
        <div class="station-info">
            <span class="station-info-icon"></span>
            <span><strong>Karachi Metropolitan Area</strong> | Last Updated: <strong>{current_time}</strong></span>
        </div>
    """, unsafe_allow_html=True)

    if df is not None and model_info is not None:
        # 2. Key Metrics (Current AQI + Model Info)
        current_aqi = df['predicted_aqi'].iloc[0]
        status_label, status_color = get_aqi_status(current_aqi)
        
        # Get model name from model_info
        model_display_name = model_info.get('model_name', 'Unknown Model')
        
        c1, c2 = st.columns(2, gap="large")
        
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Current Air Quality Index</div>
                <div class="metric-value">{current_aqi:.1f}</div>
                <div class="metric-subtext">{status_label}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Prediction Model</div>
                <div class="metric-value" style="font-size: 1.5rem;">{model_display_name}</div>
                <div class="metric-subtext">Type: {model_info.get('model_type', 'Ensemble')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("", unsafe_allow_html=True)

        # 3. 3-Day Daily Outlook with Enhanced Styling
        st.markdown("""
            <div class="section-header">
                <span class="section-icon"></span>
                <h3>3-Day Forecast Outlook</h3>
            </div>
        """, unsafe_allow_html=True)
        
        df['date'] = df['forecast_time'].dt.date
        daily_df = df.groupby('date')['predicted_aqi'].mean().reset_index()
        
        d_cols = st.columns(len(daily_df), gap="medium")
        for idx, row in daily_df.iterrows():
            with d_cols[idx]:
                day_str = row['date'].strftime('%A')
                date_str = row['date'].strftime('%d %b')
                aqi_val = row['predicted_aqi']
                status_emoji, _ = get_aqi_status(aqi_val)
                
                st.markdown(f"""
                    <div class="day-container">
                        <div class="day-name">{day_str}</div>
                        <div class="day-date">{date_str}</div>
                        <div class="day-aqi">{aqi_val:.0f}</div>
                        <div class="day-status">{status_emoji}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("", unsafe_allow_html=True)

        # 4. Hourly High-Resolution Trend with Professional Styling
        st.markdown("""
            <div class="section-header">
                <span class="section-icon"></span>
                <h3>Hourly Trend Analysis</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['forecast_time'], 
            y=df['predicted_aqi'],
            mode='lines', 
            fill='tozeroy',
            fillcolor='rgba(15, 98, 254, 0.15)',
            line=dict(
                color='#0F62FE', 
                width=3,
                shape='spline'
            ),
            name='AQI Level',
            hovertemplate='<b style="font-size:14px">AQI Level</b><br>%{y:.1f}<br><b>%{x|%H:%M on %a, %d %b}</b><extra></extra>'
        ))

        # Add threshold lines for reference
        fig.add_hline(y=50, line_dash="dash", line_color="#24A148", opacity=0.3, annotation_text="Good")
        fig.add_hline(y=100, line_dash="dash", line_color="#F1C21B", opacity=0.3, annotation_text="Moderate")
        fig.add_hline(y=150, line_dash="dash", line_color="#FF8C00", opacity=0.3, annotation_text="Unhealthy")

        fig.update_layout(
            height=380,
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family='Sora, sans-serif',
                size=13,
                color='#8B949E'
            ),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(48, 54, 61, 0.3)',
                color='#8B949E',
                tickfont=dict(size=12),
                zeroline=False
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(48, 54, 61, 0.3)',
                color='#8B949E',
                tickfont=dict(size=12),
                zeroline=False,
                range=[0, 5]
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='#161B22',
                font_size=14,
                font_family='Sora, sans-serif',
                namelength=-1
            ),
            legend=dict(
                bgcolor='rgba(22, 27, 34, 0.8)',
                bordercolor='#30363D',
                borderwidth=1,
                font=dict(size=12),
                x=0.02,
                y=0.98
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': False,
            'responsive': True
        })
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 5. Data Quality & Footer with Actual Model Info
        inference_source = model_info.get('source', 'inference')
        inference_time = model_info.get('inference_time', 'Unknown')
        model_name = model_info.get('model_name', 'Unknown')
        
        st.markdown(f"""
            <div class="footer-text">
                Model Used: <strong>{model_name}</strong> | 
                Data Synced: {datetime.now().strftime('%d %B %Y at %H:%M PKT')} | 
                Region: Karachi Metropolitan Area
            </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #DA1E28 0%, #A21E1E 100%);
                border: 1px solid #DA1E28;
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                color: white;
            ">
                <h3 style="margin: 0 0 8px 0; font-family: 'Poppins', sans-serif;">Data Not Available</h3>
                <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 0.95rem;">
                    The inference pipeline hasn't generated forecast data yet. Please ensure the data pipeline is running.
                </p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
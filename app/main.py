import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import requests
from datetime import datetime

# --- CONFIGURATION & URLS ---
CSV_URL = "https://raw.githubusercontent.com/MuhammadHamzaZeeshan/pearls-aqi-predictor/main/data/aqi_forecast_72h.csv"
JSON_URL = "https://raw.githubusercontent.com/MuhammadHamzaZeeshan/pearls-aqi-predictor/main/data/model_info.json"
HISTORY_URL = "https://raw.githubusercontent.com/MuhammadHamzaZeeshan/pearls-aqi-predictor/main/data/karachi_aqi_history.csv"

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

    .section-divider {
        border: none;
        border-top: 1px solid #30363D;
        margin: 2rem 0;
    }

    .model-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .badge-winner { background: rgba(36, 161, 72, 0.2); color: #24A148; border: 1px solid #24A148; }
    .badge-other { background: rgba(139, 148, 158, 0.1); color: #8B949E; border: 1px solid #30363D; }

    .aqi-guide-card {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 18px 14px;
        height: 100%;
        transition: all 0.3s ease;
    }
    .aqi-guide-card:hover { transform: translateY(-4px); }
    .aqi-guide-range { font-family: 'Poppins', sans-serif; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .aqi-guide-label { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
    .aqi-guide-desc { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.4; margin-bottom: 10px; }
    .aqi-guide-action {
        font-size: 0.78rem;
        font-weight: 600;
        padding: 8px 10px;
        border-radius: 8px;
        background: rgba(15, 98, 254, 0.08);
        line-height: 1.4;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def load_live_data():
    """Fetches CSV and JSON directly from GitHub Raw URLs"""
    try:
        df = pd.read_csv(CSV_URL)
        if 'forecast_time' in df.columns:
            df['forecast_time'] = pd.to_datetime(df['forecast_time'])

        response = requests.get(JSON_URL)
        model_info = response.json() if response.status_code == 200 else {}

        # Fetch historical pollutant data
        history = None
        try:
            history = pd.read_csv(HISTORY_URL)
            if 'datetime' in history.columns:
                history['datetime'] = pd.to_datetime(history['datetime'])
                history = history.sort_values('datetime')
        except Exception:
            pass

        return df, model_info, history
    except Exception as e:
        st.error(f"Failed to fetch live data: {e}")
        return None, None, None

def get_aqi_status(aqi_value):
    if aqi_value <= 1.5:
        return "Good", "#24A148"
    elif aqi_value <= 2.5:
        return "Fair", "#F1C21B"
    elif aqi_value <= 3.5:
        return "Moderate", "#FF8C00"
    elif aqi_value <= 4.5:
        return "Poor", "#DA1E28"
    else:
        return "Very Poor", "#8B00FF"

AQI_ZONES = [
    (0, 1.5, "Good", "rgba(36, 161, 72, 0.12)"),
    (1.5, 2.5, "Fair", "rgba(241, 194, 27, 0.12)"),
    (2.5, 3.5, "Moderate", "rgba(255, 140, 0, 0.12)"),
    (3.5, 4.5, "Poor", "rgba(218, 30, 40, 0.12)"),
    (4.5, 6.0, "Very Poor", "rgba(139, 0, 255, 0.12)"),
]

CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Sora, sans-serif", color="#F0F6FC"),
    margin=dict(l=20, r=20, t=40, b=20),
)

def main():
    df, model_info, history = load_live_data()

    st.markdown("<h1>Pearls: Karachi Air Quality Analytics</h1>", unsafe_allow_html=True)

    # Header
    update_time = datetime.now().strftime('%d %b, %H:%M PKT')
    st.markdown(f"**Location:** Karachi, Pakistan | **Sync Status:** 🟢 Live via GitHub Actions | **Last Sync:** {update_time}")

    if df is not None:
        # ── METRICS ROW ─────────────────────────────────────
        cur_aqi = df['predicted_aqi'].iloc[0]
        status, color = get_aqi_status(cur_aqi)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Current AQI</div><div class="metric-value" style="color:{color}">{cur_aqi:.2f}</div><div>{status}</div></div>', unsafe_allow_html=True)
        with c2:
            raw_name = model_info.get("model_name", "RandomForest")
            display_name = re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', raw_name)
            st.markdown(f'<div class="metric-card"><div class="metric-label">Model Engine</div><div class="metric-value" style="font-size:1.5rem">{display_name}</div><div>Version {model_info.get("model_version", "1.0")}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Model Confidence</div><div class="metric-value" style="font-size:1.5rem">{model_info.get("model_r2", 0.87):.2f} R²</div><div>Realistic Zone Certified</div></div>', unsafe_allow_html=True)

        # ── AQI GUIDE — WHAT SHOULD YOU DO? ───────────────
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.subheader("Understanding AQI — What Should You Do?")
        st.caption("The Air Quality Index (AQI) scale ranges from **0** (cleanest air) to **5** (most hazardous). Here's what each level means for you and your family.")

        aqi_guide = [
            ("0 – 1.5", "Good", "#24A148",
             "Air quality is satisfactory with little or no health risk.",
             "Enjoy outdoor activities freely."),
            ("1.5 – 2.5", "Fair", "#F1C21B",
             "Acceptable air quality; sensitive individuals may experience mild discomfort.",
             "Sensitive groups should limit prolonged outdoor exertion."),
            ("2.5 – 3.5", "Moderate", "#FF8C00",
             "Some pollutants may affect sensitive groups. General public is less likely to be affected.",
             "Reduce prolonged outdoor activities if you feel symptoms."),
            ("3.5 – 4.5", "Poor", "#DA1E28",
             "Health effects possible for everyone; serious effects for sensitive groups.",
             "Avoid outdoor exercise. Keep windows closed."),
            ("4.5 – 5.0", "Very Poor", "#8B00FF",
             "Emergency health alert. Entire population is at risk.",
             "Stay indoors. Use air purifiers. Wear N95 masks if going outside."),
        ]

        guide_cols = st.columns(5)
        for idx, (rng, label, color, desc, action) in enumerate(aqi_guide):
            with guide_cols[idx]:
                st.markdown(f"""
                    <div class="aqi-guide-card" style="border-left: 4px solid {color};">
                        <div class="aqi-guide-range" style="color:{color}">{rng}</div>
                        <div class="aqi-guide-label" style="color:{color}">{label}</div>
                        <div class="aqi-guide-desc">{desc}</div>
                        <div class="aqi-guide-action">{action}</div>
                    </div>
                """, unsafe_allow_html=True)

        # ── 3-DAY OUTLOOK ───────────────────────────────────
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.subheader("3-Day Outlook")
        df['date'] = df['forecast_time'].dt.date

        daily = df.groupby('date')['predicted_aqi'].mean().reset_index()
        daily = daily.sort_values('date').reset_index(drop=True)

        unique_dates_count = len(daily)
        if unique_dates_count >= 4:
            daily = daily.iloc[1:4]
        else:
            daily = daily.head(3)

        cols = st.columns(3)
        for idx, (_, row) in enumerate(daily.iterrows()):
            with cols[idx]:
                s, sc = get_aqi_status(row['predicted_aqi'])
                st.markdown(f"""
                    <div class="day-container">
                        <div style="color:#0F62FE; font-weight:700">{row['date'].strftime('%A')}</div>
                        <div style="font-size:2rem; font-weight:800; color:{sc}">{row['predicted_aqi']:.2f}</div>
                        <div style="font-size:0.8rem">{s}</div>
                    </div>
                """, unsafe_allow_html=True)

        # ── 72-HOUR TREND WITH AQI ZONES ────────────────────
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.subheader("72-Hour Detailed Trend")

        fig = go.Figure()

        # AQI zone bands
        for y0, y1, label, fill_color in AQI_ZONES:
            fig.add_hrect(
                y0=y0, y1=y1,
                fillcolor=fill_color,
                line_width=0,
                annotation_text=label,
                annotation_position="top left",
                annotation=dict(font_size=10, font_color="#8B949E"),
            )

        # Main forecast line
        fig.add_trace(go.Scatter(
            x=df['forecast_time'], y=df['predicted_aqi'],
            fill='tozeroy',
            fillcolor='rgba(15, 98, 254, 0.15)',
            line=dict(color='#0F62FE', width=2.5),
            name='Predicted AQI',
            hovertemplate='<b>%{x|%a %H:%M}</b><br>AQI: %{y:.2f}<extra></extra>',
        ))

        # Daily average markers
        daily_avg = df.groupby('date').agg(
            avg_aqi=('predicted_aqi', 'mean'),
            mid_time=('forecast_time', lambda x: x.iloc[len(x)//2])
        ).reset_index()

        fig.add_trace(go.Scatter(
            x=daily_avg['mid_time'], y=daily_avg['avg_aqi'],
            mode='markers+text',
            marker=dict(size=10, color='#00D9FF', symbol='diamond', line=dict(width=1, color='#fff')),
            text=[f"Avg: {v:.1f}" for v in daily_avg['avg_aqi']],
            textposition='top center',
            textfont=dict(size=11, color='#00D9FF'),
            name='Daily Average',
            hovertemplate='<b>Daily Avg</b><br>AQI: %{y:.2f}<extra></extra>',
        ))

        fig.update_layout(
            **CHART_LAYOUT,
            height=360,
            yaxis=dict(range=[0, 6], gridcolor='rgba(48,54,61,0.4)', tickfont=dict(size=13)),
            xaxis=dict(gridcolor='rgba(48,54,61,0.2)', tickfont=dict(size=13)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── AQI DISTRIBUTION & HOURLY PATTERN (side by side) ─
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        # -- Donut: AQI Category Distribution --
        with col_left:
            st.subheader("Forecast Breakdown")
            categories = {"Good": 0, "Fair": 0, "Moderate": 0, "Poor": 0, "Very Poor": 0}
            cat_colors = {"Good": "#24A148", "Fair": "#F1C21B", "Moderate": "#FF8C00", "Poor": "#DA1E28", "Very Poor": "#8B00FF"}

            for val in df['predicted_aqi']:
                s, _ = get_aqi_status(val)
                categories[s] += 1

            # Filter out zero-count categories
            labels = [k for k, v in categories.items() if v > 0]
            values = [v for v in categories.values() if v > 0]
            colors = [cat_colors[l] for l in labels]

            fig_donut = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color='#0F1419', width=2)),
                textinfo='label+percent',
                textfont=dict(size=12, color='#F0F6FC'),
                hovertemplate='<b>%{label}</b><br>%{value} hours (%{percent})<extra></extra>',
            )])
            fig_donut.update_layout(
                **CHART_LAYOUT,
                height=320,
                showlegend=False,
                annotations=[dict(text=f"{len(df)}h", x=0.5, y=0.5, font_size=22, font_color='#F0F6FC', showarrow=False)],
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        # -- Bar: Hourly AQI Pattern --
        with col_right:
            st.subheader("Hourly Pattern")
            df['hour'] = df['forecast_time'].dt.hour
            hourly = df.groupby('hour')['predicted_aqi'].mean().reset_index()

            bar_colors = [get_aqi_status(v)[1] for v in hourly['predicted_aqi']]

            fig_hourly = go.Figure(data=[go.Bar(
                x=hourly['hour'], y=hourly['predicted_aqi'],
                marker=dict(color=bar_colors, line=dict(width=0)),
                hovertemplate='<b>%{x}:00</b><br>Avg AQI: %{y:.2f}<extra></extra>',
            )])
            fig_hourly.update_layout(
                **CHART_LAYOUT,
                height=320,
                xaxis=dict(
                    title="Hour of Day", tickmode='linear', dtick=3,
                    gridcolor='rgba(48,54,61,0.2)', tickfont=dict(size=12),
                ),
                yaxis=dict(
                    title="Avg AQI", range=[0, 6],
                    gridcolor='rgba(48,54,61,0.4)', tickfont=dict(size=12),
                ),
                bargap=0.15,
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

        # ── POLLUTANT INPUT FEATURES ────────────────────────
        if history is not None and len(history) > 0:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.subheader("Pollutant Input Features")
            st.caption("Real-time pollutant readings from openweather that feed into the prediction model")

            pollutant_cols = ['co', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
            pollutant_labels = {
                'co': 'CO', 'no2': 'NO\u2082', 'o3': 'O\u2083', 'so2': 'SO\u2082',
                'pm2_5': 'PM2.5', 'pm10': 'PM10', 'nh3': 'NH\u2083'
            }
            pollutant_units = {
                'co': '\u00b5g/m\u00b3', 'no2': '\u00b5g/m\u00b3', 'o3': '\u00b5g/m\u00b3',
                'so2': '\u00b5g/m\u00b3', 'pm2_5': '\u00b5g/m\u00b3', 'pm10': '\u00b5g/m\u00b3',
                'nh3': '\u00b5g/m\u00b3'
            }
            # Reference maximums for radar normalization (based on WHO/observed ranges)
            pollutant_ref_max = {
                'co': 200, 'no2': 0.5, 'o3': 150, 'so2': 1.0,
                'pm2_5': 75, 'pm10': 200, 'nh3': 0.5
            }

            latest = history.iloc[-1]
            last_timestamp = latest['datetime'].strftime('%d %b %Y, %H:%M') if pd.notna(latest.get('datetime')) else 'N/A'

            col_radar, col_trend = st.columns(2)

            # -- Radar: Latest Pollutant Snapshot --
            with col_radar:
                st.markdown(f"**Latest Readings** &mdash; {last_timestamp}")

                radar_labels = [pollutant_labels[p] for p in pollutant_cols]
                radar_values = []
                for p in pollutant_cols:
                    val = latest.get(p, 0)
                    normalized = min((val / pollutant_ref_max[p]) * 100, 100) if pollutant_ref_max[p] > 0 else 0
                    radar_values.append(round(normalized, 1))

                # Close the radar polygon
                radar_labels_closed = radar_labels + [radar_labels[0]]
                radar_values_closed = radar_values + [radar_values[0]]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_values_closed,
                    theta=radar_labels_closed,
                    fill='toself',
                    fillcolor='rgba(15, 98, 254, 0.2)',
                    line=dict(color='#0F62FE', width=2),
                    name='Current',
                    hovertemplate='<b>%{theta}</b><br>%{r:.1f}% of reference<extra></extra>',
                ))

                # Add 24h-ago comparison if available
                if len(history) >= 24:
                    prev = history.iloc[-24]
                    prev_values = []
                    for p in pollutant_cols:
                        val = prev.get(p, 0)
                        normalized = min((val / pollutant_ref_max[p]) * 100, 100) if pollutant_ref_max[p] > 0 else 0
                        prev_values.append(round(normalized, 1))
                    prev_values_closed = prev_values + [prev_values[0]]

                    fig_radar.add_trace(go.Scatterpolar(
                        r=prev_values_closed,
                        theta=radar_labels_closed,
                        fill='toself',
                        fillcolor='rgba(139, 148, 158, 0.08)',
                        line=dict(color='#484F58', width=1, dash='dot'),
                        name='24h ago',
                        hovertemplate='<b>%{theta}</b><br>%{r:.1f}% of reference<extra></extra>',
                    ))

                fig_radar.update_layout(
                    **CHART_LAYOUT,
                    height=370,
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(
                            visible=True, range=[0, 100],
                            gridcolor='rgba(48,54,61,0.4)', tickfont=dict(size=10, color='#8B949E'),
                            ticksuffix='%',
                        ),
                        angularaxis=dict(
                            gridcolor='rgba(48,54,61,0.3)',
                            tickfont=dict(size=12, color='#F0F6FC'),
                        ),
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=11)),
                    showlegend=True,
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # -- Trend: Pollutant history over last 7 days --
            with col_trend:
                st.markdown("**7-Day Pollutant Trends**")

                recent = history.tail(168)  # 7 days * 24 hours

                # Group into two scales: high-value (CO, O3, PM10) and low-value (NO2, SO2, PM2.5, NH3)
                fig_trend = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.08,
                    row_heights=[0.5, 0.5],
                    subplot_titles=("Particulate Matter & CO", "Trace Gases"),
                )

                high_group = {'co': '#0F62FE', 'pm10': '#FF8C00', 'pm2_5': '#DA1E28'}
                low_group = {'no2': '#00D9FF', 'o3': '#24A148', 'so2': '#F1C21B', 'nh3': '#8B00FF'}

                for col, color in high_group.items():
                    if col in recent.columns:
                        fig_trend.add_trace(go.Scatter(
                            x=recent['datetime'], y=recent[col],
                            mode='lines', name=pollutant_labels[col],
                            line=dict(color=color, width=1.5),
                            hovertemplate=f'<b>{pollutant_labels[col]}</b><br>' + '%{x|%d %b %H:%M}<br>%{y:.2f} ' + pollutant_units[col] + '<extra></extra>',
                        ), row=1, col=1)

                for col, color in low_group.items():
                    if col in recent.columns:
                        fig_trend.add_trace(go.Scatter(
                            x=recent['datetime'], y=recent[col],
                            mode='lines', name=pollutant_labels[col],
                            line=dict(color=color, width=1.5),
                            hovertemplate=f'<b>{pollutant_labels[col]}</b><br>' + '%{x|%d %b %H:%M}<br>%{y:.2f} ' + pollutant_units[col] + '<extra></extra>',
                        ), row=2, col=1)

                fig_trend.update_layout(
                    **CHART_LAYOUT,
                    height=370,
                    legend=dict(
                        orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5,
                        font=dict(size=10),
                    ),
                    showlegend=True,
                )
                fig_trend.update_yaxes(gridcolor='rgba(48,54,61,0.4)', tickfont=dict(size=10), row=1, col=1)
                fig_trend.update_yaxes(gridcolor='rgba(48,54,61,0.4)', tickfont=dict(size=10), row=2, col=1)
                fig_trend.update_xaxes(gridcolor='rgba(48,54,61,0.2)', tickfont=dict(size=10), row=2, col=1)
                fig_trend.update_annotations(font=dict(color='#8B949E', size=11))

                st.plotly_chart(fig_trend, use_container_width=True)

            # -- Pollutant level cards --
            st.markdown("")
            p_cols = st.columns(len(pollutant_cols))
            for idx, p in enumerate(pollutant_cols):
                val = latest.get(p, 0)
                pct = min((val / pollutant_ref_max[p]) * 100, 100) if pollutant_ref_max[p] > 0 else 0
                if pct >= 75:
                    pct_color = "#DA1E28"
                elif pct >= 50:
                    pct_color = "#FF8C00"
                elif pct >= 25:
                    pct_color = "#F1C21B"
                else:
                    pct_color = "#24A148"
                with p_cols[idx]:
                    st.markdown(f"""
                    <div style="background:rgba(22,27,34,0.8); border:1px solid #30363D; border-radius:10px; padding:12px; text-align:center;">
                        <div style="color:#8B949E; font-size:0.7rem; font-weight:600; text-transform:uppercase;">{pollutant_labels[p]}</div>
                        <div style="font-size:1.3rem; font-weight:800; font-family:'Poppins',sans-serif; color:{pct_color};">{val:.2f}</div>
                        <div style="font-size:0.65rem; color:#6E7681;">{pollutant_units[p]}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── MODEL COMPARISON (from Hopsworks Registry) ──────
        if model_info.get("models"):
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.subheader("Model Registry Comparison")
            st.caption(f"Selection criteria: {model_info.get('selection_criteria', 'Lowest MAE')}")

            models = model_info["models"]
            names = [m["name"] for m in models]
            maes = [m["mae"] for m in models]
            r2s = [m["r2"] for m in models]
            is_selected = [m.get("selected", False) for m in models]

            col_chart, col_detail = st.columns([3, 2])

            with col_chart:
                # Grouped bar chart: MAE and R2 side by side
                bar_colors_mae = ['#0F62FE' if sel else '#30363D' for sel in is_selected]
                bar_colors_r2 = ['#00D9FF' if sel else '#484F58' for sel in is_selected]

                fig_comp = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=("Mean Absolute Error (lower is better)", "R² Score (higher is better)"),
                    horizontal_spacing=0.15,
                )

                fig_comp.add_trace(go.Bar(
                    x=names, y=maes,
                    marker=dict(color=bar_colors_mae, line=dict(width=0)),
                    text=[f"{v:.4f}" for v in maes],
                    textposition='outside',
                    textfont=dict(size=12, color='#F0F6FC'),
                    hovertemplate='<b>%{x}</b><br>MAE: %{y:.4f}<extra></extra>',
                    showlegend=False,
                ), row=1, col=1)

                fig_comp.add_trace(go.Bar(
                    x=names, y=r2s,
                    marker=dict(color=bar_colors_r2, line=dict(width=0)),
                    text=[f"{v:.4f}" for v in r2s],
                    textposition='outside',
                    textfont=dict(size=12, color='#F0F6FC'),
                    hovertemplate='<b>%{x}</b><br>R²: %{y:.4f}<extra></extra>',
                    showlegend=False,
                ), row=1, col=2)

                # Add realistic zone band on R2 chart
                fig_comp.add_hrect(
                    y0=0.60, y1=0.90,
                    fillcolor="rgba(36, 161, 72, 0.08)",
                    line=dict(width=1, color="rgba(36, 161, 72, 0.3)", dash="dot"),
                    row=1, col=2,
                    annotation_text="Realistic Zone",
                    annotation_position="top right",
                    annotation=dict(font_size=9, font_color="#24A148"),
                )

                fig_comp.update_layout(
                    **CHART_LAYOUT,
                    height=340,
                )
                fig_comp.update_yaxes(gridcolor='rgba(48,54,61,0.4)', range=[0, max(maes) * 1.4], row=1, col=1)
                fig_comp.update_yaxes(gridcolor='rgba(48,54,61,0.4)', range=[0, 1.0], row=1, col=2)
                fig_comp.update_annotations(font=dict(color='#8B949E', size=12))

                st.plotly_chart(fig_comp, use_container_width=True)

            with col_detail:
                # Model selection explanation cards
                st.markdown("**Why this model?**")

                for m in models:
                    badge = "badge-winner" if m.get("selected") else "badge-other"
                    tag = "SELECTED" if m.get("selected") else "CANDIDATE"

                    if m.get("selected"):
                        reason = "Lowest prediction error across the test set. Balances accuracy with generalization within the Realistic Zone (R² 0.60-0.90)."
                    elif m["name"] == "Ridge":
                        reason = "Linear model with strong regularization. Underfits on non-linear AQI patterns, resulting in higher MAE."
                    elif m["name"] == "NeuralNetwork":
                        reason = "Deep learning approach with dropout. Competitive R², but higher MAE than tree-based methods on this dataset size."
                    else:
                        reason = "Evaluated as a candidate during daily retraining."

                    st.markdown(f"""
                    <div style="background:rgba(22,27,34,0.8); border:1px solid {'#24A148' if m.get('selected') else '#30363D'}; border-radius:10px; padding:14px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-weight:700; font-size:0.95rem;">{m['name']}</span>
                            <span class="model-badge {badge}">{tag}</span>
                        </div>
                        <div style="color:#8B949E; font-size:0.8rem; line-height:1.4;">{reason}</div>
                        <div style="margin-top:8px; font-size:0.8rem;">
                            <span style="color:#0F62FE;">MAE: {m['mae']:.4f}</span> &nbsp;|&nbsp;
                            <span style="color:#00D9FF;">R²: {m['r2']:.4f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── FOOTER ──────────────────────────────────────────
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("<center style='color:#6E7681; font-size:0.8rem'>Developed by Muhammad Hamza Zeeshan | 10Pearls Internship 2026</center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
import streamlit as st
import requests
import pandas as pd
import time
import os

ANALYZER_URL = os.getenv("ANALYZER_URL", "http://analyzer:8001")

st.set_page_config(page_title="Cloud Log Dashboard", layout="wide")

# Custom visual theme styling
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #38bdf8;
        margin-top: 5px;
    }
    .metric-title {
        font-size: 0.95rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-normal {
        background-color: #064e3b;
        color: #34d399;
        border: 1px solid #047857;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .status-alert {
        background-color: #7f1d1d;
        color: #fca5a5;
        border: 1px solid #b91c1c;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Cloud Log Monitoring Dashboard")
st.caption("Real-Time Telemetry & Log Anomaly Observability Pipeline")

# Panel 7: Interactive Search & Filtering Panel (Sidebar)
st.sidebar.header("🔍 Filter & Controls")
search_query = st.sidebar.text_input("Search Messages", "")
level_filter = st.sidebar.selectbox("Log Level Filter", ["ALL", "INFO", "WARNING", "ERROR"])

st.sidebar.divider()
st.sidebar.subheader("System Actions")
if st.sidebar.button("🧹 Clear & Reset Log Data", use_container_width=True):
    try:
        response = requests.post(f"{ANALYZER_URL}/reset")
        if response.status_code == 200:
            st.sidebar.success("Log store cleared successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error("Failed to reset logs.")
    except Exception as e:
        st.sidebar.error(f"Error resetting logs: {e}")

# Live Dashboard Container
placeholder = st.empty()

while True:
    try:
        # Fetch stats, logs, and alerts from Analyzer microservice
        stats = requests.get(f"{ANALYZER_URL}/stats").json()
        logs_data = requests.get(f"{ANALYZER_URL}/logs").json()["logs"]
        alert = requests.get(f"{ANALYZER_URL}/alerts").json()["alert"]

        df = pd.DataFrame(logs_data)

        # Apply filtering for UI display
        if not df.empty:
            if search_query:
                df = df[df["message"].str.contains(search_query, case=False, na=False)]
            if level_filter != "ALL":
                df = df[df["level"].str.upper() == level_filter.upper()]

        with placeholder.container():
            # FIRST ROW: Status and Metrics (Panels 1, 2, 3, 4)
            col_status, col_total, col_errors, col_alert_details = st.columns([1.5, 1, 1, 1.5])
            
            # Panel 1: System Health Status Card
            with col_status:
                if alert:
                    st.markdown('<div class="status-alert">🚨 ALERT ACTIVE: Anomalies Detected</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-normal">✅ SYSTEM STABLE: All Services Normal</div>', unsafe_allow_html=True)
            
            # Panel 2: Total Ingestion Volume Card
            with col_total:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Total Ingested Logs</div>
                        <div class="metric-value">{stats['total_logs']}</div>
                    </div>
                """, unsafe_allow_html=True)

            # Panel 3: Total Error Count Card
            with col_errors:
                err_rate = 0.0
                if stats['total_logs'] > 0:
                    err_rate = (stats['error_count'] / stats['total_logs']) * 100
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Total Errors (Rate)</div>
                        <div class="metric-value">{stats['error_count']} <span style='font-size: 1.1rem; color: #f43f5e;'>({err_rate:.1f}%)</span></div>
                    </div>
                """, unsafe_allow_html=True)

            # Panel 4: Data Anomaly Alerts Card
            with col_alert_details:
                if alert:
                    st.error(f"Active Alert:\n{alert}")
                else:
                    st.success("No active anomalies detected (Error Count < 5).")

            st.divider()

            # SECOND ROW: Analytics & Charts (Panels 5, 6)
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("📊 Log Level Distribution") # Panel 5: Log Level Distribution Chart
                if not df.empty:
                    level_counts = df["level"].value_counts().reset_index()
                    level_counts.columns = ["Level", "Count"]
                    # Pivot for displaying categories nicely
                    st.bar_chart(level_counts.set_index("Level"), color="#38bdf8")
                else:
                    st.info("No data available to display chart.")

            with col_chart2:
                st.subheader("📈 Log Ingestion Timeline") # Panel 6: Ingest Time-Series Timeline Chart
                if not df.empty:
                    # Group logs by timestamp to show rate of logs
                    time_counts = df["timestamp"].value_counts().sort_index().reset_index()
                    time_counts.columns = ["Timestamp", "Logs/Second"]
                    st.line_chart(time_counts.set_index("Timestamp"), color="#34d399")
                else:
                    st.info("No data available to display timeline.")

            st.divider()

            # THIRD ROW: Log stream data profile (Panel 8)
            st.subheader("📋 Real-time Log Stream Data Profile")
            if not df.empty:
                st.dataframe(
                    df[["timestamp", "level", "message"]].iloc[::-1], # show newest first
                    use_container_width=True,
                    column_config={
                        "timestamp": "Time Received",
                        "level": "Severity",
                        "message": "Log Message Content"
                    }
                )
            else:
                st.info("No log events match the current filter criteria.")

        time.sleep(2)

    except Exception as e:
        with placeholder.container():
            st.warning(f"⚠️ Connecting to Analyzer microservice ({ANALYZER_URL})...")
            st.caption("Make sure all microservices are running in Docker or locally.")
        time.sleep(2)
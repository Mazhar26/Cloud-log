import streamlit as st
import requests
import pandas as pd
import time

ANALYZER_URL = "http://analyzer:8001"

st.set_page_config(page_title="Cloud Log Dashboard", layout="wide")

st.title("🚀 Cloud Log Monitoring Dashboard")

# Auto refresh
placeholder = st.empty()

while True:
    try:
        stats = requests.get(f"{ANALYZER_URL}/stats").json()
        logs = requests.get(f"{ANALYZER_URL}/logs").json()["logs"]
        alert = requests.get(f"{ANALYZER_URL}/alerts").json()["alert"]

        with placeholder.container():

            # Metrics
            col1, col2 = st.columns(2)
            col1.metric("Total Logs", stats["total_logs"])
            col2.metric("Error Count", stats["error_count"])

            st.divider()

            # Alert
            if alert:
                st.error(alert)
            else:
                st.success("✅ System Normal")

            st.divider()

            # Logs Table
            df = pd.DataFrame(logs)
            st.subheader("Recent Logs")
            st.dataframe(df, use_container_width=True)

        time.sleep(2)

    except:
        st.warning("⚠️ Analyzer not reachable")
        time.sleep(2)
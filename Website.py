import Streamlit as st 
import pandas as pd 
import yfinance as yf 
from datetime import datetime, timedelta
import time 

#  Streamlit Page Config
st.set_page_config(
     page_title="OpenFX Live Dashboard", layout="wide" 
     )

st.title("OpenFX Live Volatility Dashboard") 
st.write("Real‑time FX monitoring with alerts and live charts.") 

#  Fetch FX Data 
@st.cache_data(ttl=60) 
def get_live_fx(pair="EURUSD=X"): 
    try:
        ticker = yf.Ticker(pair) 
        df = ticker.history(period="1d", interval="1m")
        return df if not df.empty else pd.DataFrame()
    except: 
        return pd.DataFrame()

# Percent Change 
def calculate_percent_change(df, lookback=5):
    if len(df) < lookback:
        return 0.0
    current_price = df["Close"].iloc[-1]
    old_price = df["Close"].iloc[-lookback]
    return ((current_price - old_price) / old_price) * 100

# Alert Logic 
def classify_alert(pct):
    if abs(pct) < 0.1:
        return None
    if abs(pct) < 0.5:
        return "minor"
    return "major"

# Sidebar Controls 
st.sidebar.header("Settings")

default_pairs = [
    "EURUSD=X", 
    "USDJPY=X", 
    "GBPUSD=X", 
    "USDCHF=X", 
    "USDCAD=X", 
    "AUDUSD=X"
]
pairs = st.sidebar.multiselect( 
    "Select FX Pairs", 
    default_pairs,
    default_pairs 
)
lookback = st.sidebar.slider(
     "Lookback (minutes)", 
     1, 30, 5 
)

refresh_rate = st.sidebar.slider(
    "Refresh every (seconds)",
    10, 120, 60 
)

st.sidebar.info("Dashboard auto‑refreshes when you click **Run**.")

# Main Dashboard 
placeholder = st.empty()

while True: 
    with placeholder.container():
        st.subheader(f"Live FX Prices (Updated {datetime.now().strftime('%H:%M:%S')})") 
        cols = st.columns(len(pairs))

        alert_messages = []

        #Loop through each FX pair
        
        for i, pair in enumerate(pairs):
            df = get_live_fx(pair)

            if df.empty:
                cols[i].warning(f"{pair.replace('=X','')}: No data")
                continue

            pct = calculate_percent_change(df, lookback)
            price = df["Close"].iloc[-1]
            alert_type = classify_alert(pct)

            #Display metric
            delta_color = "normal" if pct >= 0 else "inverse"
            cols[i].metric(
                label = pair.replace("=X", ""),
                value=f"{price:.5f}",
                delta=f"{pct:+.2f}%",
                delta_color=delta_color
            )

            # Collect alerts
            if alert_type:
                alert_messages.append(pair, pct, price, alert_type)

            st.divider()

            
            # Alerts Section
            
            st.header("Alerts")
            
            if not alert_messages:
                st.success("No alerts triggered")
            else:
                for pair, pct, price, alert_type in alert_messages:
                    if alert_type == "minor":
                        st.warning(
                            f"**MINOR ALERT – {pair.replace('=X','')}**\n\n"
                            f"Price: `{price:.5f}`\n"
                            f"Move: `{pct:+.2f}%`"
                        )
                    else:
                        st.error(
                            f"**MAJOR ALERT – {pair.replace('=X','')}**\n\n" 
                            f"Price: `{price:.5f}`\n" 
                            f"Move: `{pct:+.2f}%`"
                        )
            st.divider()

            
            # Charts Section
            
            st.header("Price Charts")
            
            for pair in pairs:
                df = get_live_fx(pair) 
                if df.empty: 
                    continue 
                
                st.subheader(pair.replace("=X", "")) 
                st.line_chart(df["Close"]) 
                
            time.sleep(refresh_rate)
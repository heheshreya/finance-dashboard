import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Setup
st.set_page_config(page_title="Pro Finance Dashboard", layout="wide")

# 2. Sidebar Configuration
st.sidebar.header("🛠️ Dashboard Settings")
stock = st.sidebar.selectbox("Select Stock", ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"])
chart_type = st.sidebar.radio("Chart Style", ["Line", "Candlestick"])

st.sidebar.divider()
st.sidebar.header("💰 My Portfolio")
shares_owned = st.sidebar.number_input("Shares Owned", min_value=0, value=0)
buy_price = st.sidebar.number_input("Average Buy Price", min_value=0.0, value=0.0)

# 3. Data Engine
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="2y")
    # Check if we got data back
    if df.empty:
        return pd.DataFrame() # Return empty if nothing found
        
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI Logic
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain/loss)))
    return df

df = get_data(stock)

# --- THE SAFETY GATE ---
if df.empty:
    st.error(f"No data found for {stock}. Please check the ticker symbol or try again later.")
else:
    # MOVE ALL YOUR KPI AND CHART CODE INSIDE THIS 'ELSE' BLOCK
    latest = df.iloc[-1]
    prev_close = df.iloc[-2]['Close']
    
    # ... (Rest of your KPI, Signal, and Chart code) ...

df = get_data(stock)
latest = df.iloc[-1]
prev_close = df.iloc[-2]['Close']

# --- Safe Company Info Fetch ---
try:
    ticker_info = yf.Ticker(stock)
    # This .info line is the one causing the RateLimitError
    company_name = ticker_info.info.get('longName', stock)
    company_summary = ticker_info.info.get('longBusinessSummary', "No summary available.")
    
    st.subheader(f"About {company_name}")
    with st.expander("Read Business Summary"):
        st.write(company_summary)
except Exception:
    # If Yahoo blocks us, just show the Ticker name and move on
    st.subheader(f"About {stock}")
    st.info("Company summary temporarily unavailable due to Yahoo Finance rate limits.")
# Display it in the app
st.subheader(f"About {company_name}")
with st.expander("Read Business Summary"):
    st.write(company_summary)

# 4. KPI Header
st.title(f"🔍 {stock} Analysis")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# Current Price & Change
price_change = latest['Close'] - prev_close
pct_change = (price_change / prev_close) * 100
kpi1.metric("Live Price", f"${latest['Close']:,.2f}", f"{pct_change:.2f}%")

# Portfolio Logic
if shares_owned > 0:
    current_val = shares_owned * latest['Close']
    total_cost = shares_owned * buy_price
    total_pl = current_val - total_cost
    kpi2.metric("Portfolio Value", f"${current_val:,.2f}", f"${total_pl:,.2f} Total P/L")
else:
    kpi2.metric("Portfolio Value", "$0.00", "No shares entered")

kpi3.metric("RSI (14)", f"{latest['RSI']:.1f}", help="Over 70 is Overbought, Under 30 is Oversold")

# Signal logic
if latest['Close'] > latest['MA50'] and latest['RSI'] < 45:
    sig, col = "BUY", "green"
elif latest['RSI'] > 70:
    sig, col = "SELL", "red"
else:
    sig, col = "HOLD", "gray"
kpi4.subheader(f"Signal: :{col}[{sig}]")

# 5. Main Chart Section
col1, col2, col3 = st.columns([0.05, 0.9, 0.05])
with col2:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # Plot Price (Line or Candlestick)
    if chart_type == "Line":
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='#00d4ff')), row=1, col=1)
    else:
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50", line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#833ab4')), row=2, col=1)

    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# 6. Export and Raw Data
st.divider()
down_col1, down_col2 = st.columns([1, 4])
with down_col1:
    csv = df.to_csv().encode('utf-8')
    st.download_button("📥 Download CSV Data", data=csv, file_name=f"{stock}_data.csv", mime='text/csv')
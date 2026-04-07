import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Setup
st.set_page_config(page_title="Financial Dashboard Pro", layout="wide")

# 2. Sidebar
st.sidebar.header("Settings")
stock = st.sidebar.selectbox("Select a Stock", ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"])

# 3. Data Fetching & Calculations
@st.cache_data
def get_processed_data(ticker):
    df = yf.download(ticker, period="2y")
    df.columns = df.columns.droplevel(1)
    # Technical Indicators
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

df = get_processed_data(stock)
last_row = df.iloc[-1]
prev_close = df['Close'].iloc[-2]
curr_price = df['Close'].iloc[-1]
price_diff = curr_price - prev_close
pct_diff = (price_diff / prev_close) * 100

# 4. KPI Section (The "Top Bar")
# Centering the metrics
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric("Current Price", f"${curr_price:,.2f}", f"{pct_diff:.2f}%")

with m_col2:
    st.metric("50-Day MA", f"${last_row['MA50']:,.2f}")

with m_col3:
    st.metric("RSI (14)", f"{last_row['RSI']:.1f}")

with m_col4:
    # Trading Signal Logic
    if last_row['Close'] > last_row['MA50'] and last_row['RSI'] < 40:
        signal = "BUY"
        color = "green"
    elif last_row['Close'] < last_row['MA50'] or last_row['RSI'] > 70:
        signal = "SELL"
        color = "red"
    else:
        signal = "HOLD"
        color = "gray"
    
    st.subheader(f"Signal: :{color}[{signal}]")

st.divider()

# 5. Centered Chart (From Day 2)
col1, col2, col3 = st.columns([0.05, 0.9, 0.05])
with col2:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
    
    # Price and MAs
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='#00d4ff')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50", line=dict(color='orange')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#833ab4')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
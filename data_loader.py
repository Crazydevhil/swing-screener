import yfinance as yf
import pandas as pd
import requests
import io
import streamlit as st

@st.cache_data(ttl=86400) # Cache for 24 hours
def get_nifty_500_data():
    """
    Fetches the Nifty 500 list from NSE including Sector/Industry data.
    Returns a pandas DataFrame with 'Ticker' and 'Industry'.
    """
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        
        # Format ticker for yfinance
        df['Ticker'] = df['Symbol'].astype(str) + ".NS"
        
        # Ensure Industry column exists, if not, create a generic one
        if 'Industry' not in df.columns:
             df['Industry'] = 'Unknown'
             
        return df[['Ticker', 'Industry']]
    except Exception as e:
        print(f"Failed to fetch Nifty 500 from NSE: {e}")
        # Fallback dictionary
        fallback_data = [
            {"Ticker": "RELIANCE.NS", "Industry": "Oil Gas & Consumable Fuels"},
            {"Ticker": "TCS.NS", "Industry": "Information Technology"},
            {"Ticker": "HDFCBANK.NS", "Industry": "Financial Services"},
            {"Ticker": "ICICIBANK.NS", "Industry": "Financial Services"}
        ]
        return pd.DataFrame(fallback_data)

@st.cache_data(ttl=3600)
def download_historical_data(ticker, period="1y"):
    """
    Downloads historical daily stock data using yfinance.
    Requires at least 1y for robust 200 SMA and support/resistance calculations.
    Returns a pandas DataFrame.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
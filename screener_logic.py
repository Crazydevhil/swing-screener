import yfinance as yf
import pandas as pd
import ta
import requests
from io import StringIO
from datetime import datetime, timedelta

# --- CONSTANTS ---
LOOKBACK_DAYS = 365
TARGET_MULTIPLIER = 3.0

INDEX_URLS = {
    "nifty50":     "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "nifty500":    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
}

FALLBACK_LISTS = {
    "nifty50": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
        "SBIN", "BAJFINANCE", "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK",
        "ASIANPAINT", "MARUTI", "TITAN", "SUNPHARMA", "NESTLEIND", "WIPRO",
        "ULTRACEMCO", "POWERGRID", "NTPC", "TECHM", "HCLTECH", "INDUSINDBK",
        "BAJAJFINSV", "ONGC", "COALINDIA", "IOC", "BPCL", "GRASIM",
        "DIVISLAB", "DRREDDY", "CIPLA", "EICHERMOT", "HEROMOTOCO",
        "ADANIPORTS", "TATAMOTORS", "TATACONSUM", "TATASTEEL", "HINDALCO",
        "JSWSTEEL", "M&M", "BRITANNIA", "APOLLOHOSP", "BAJAJ-AUTO",
        "SHREECEM", "UPL", "SBILIFE", "HDFCLIFE", "LTIM"
    ]
}

def get_tickers(index_name):
    sector_map = {}
    tickers = []
    try:
        url = INDEX_URLS[index_name]
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        df = pd.read_csv(StringIO(response.text))
        for _, row in df.iterrows():
            ticker = row['Symbol'] + ".NS"
            industry = row.get('Industry', 'Unknown')
            tickers.append(ticker)
            sector_map[ticker] = industry
    except Exception as e:
        fallback = FALLBACK_LISTS.get(index_name, FALLBACK_LISTS["nifty50"])
        for sym in fallback:
            ticker = sym + ".NS"
            tickers.append(ticker)
            sector_map[ticker] = "Unknown"
    return tickers, sector_map

def calculate_levels(current_price, structural_stop_loss):
    entry = round(current_price, 2)
    stop_loss = round(structural_stop_loss, 2)
    risk_per_share = entry - stop_loss
    
    if risk_per_share <= 0:
        return entry, round(entry * 0.98, 2), round(entry * 1.06, 2)
        
    target = round(entry + (risk_per_share * TARGET_MULTIPLIER), 2)
    return entry, stop_loss, target

def is_bullish_engulfing(prev_open, prev_close, curr_open, curr_close):
    prev_red = prev_open > prev_close
    curr_green = curr_close > curr_open
    engulfs = (curr_open < prev_close) and (curr_close > prev_open)
    return prev_red and curr_green and engulfs

def determine_strategy(open_p, close_p, prev_open_p, prev_close_p, sma20, prev_sma20, sma50, sma200, rsi, macd_cross, adx, atr, vol, avg_vol_20d, support, resistance):
    # Strategy 1: Trend Pullback
    uptrend = (sma50 > sma200)
    strong_trend = adx > 20
    genuine_pullback = (35 <= rsi <= 60)
    near_support = ((close_p - support) / support) < 0.15
    conviction_candle = (close_p > open_p)

    if uptrend and strong_trend and genuine_pullback and near_support and conviction_candle:
        return "Trend Pullback", max((close_p - 1.5 * atr), support * 0.98)

    # Strategy 2: Momentum Breakout
    price_cross_20 = (close_p > sma20) and (prev_close_p <= prev_sma20)
    vol_surge = vol > (1.5 * avg_vol_20d)
    
    if vol_surge and (macd_cross or price_cross_20) and rsi > 55:
        return "Momentum Breakout", max((close_p - 1.5 * atr), support * 0.98)

    # Strategy 3: Support Reversal
    oversold = rsi < 45
    engulfing = is_bullish_engulfing(prev_open_p, prev_close_p, open_p, close_p)
    near_supp_strict = ((close_p - support) / support) < 0.05
    
    if oversold and engulfing and near_supp_strict:
        return "Support Reversal", max((close_p - 1.5 * atr), support * 0.98)

    return None, None

def fetch_technicals_swing(tickers, sector_map, selected_sectors=None, progress_callback=None):
    results = []
    historical_data_map = {}
    
    if selected_sectors and len(selected_sectors) > 0:
        tickers = [t for t in tickers if sector_map.get(t, "Unknown") in selected_sectors]
        
    total = len(tickers)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i, total, ticker)
            
        try:
            hist = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if len(hist) < 200:
                continue

            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)

            close  = hist['Close'].squeeze()
            open_s = hist['Open'].squeeze()
            volume = hist['Volume'].squeeze()
            high   = hist['High'].squeeze()
            low    = hist['Low'].squeeze()

            current_close = float(close.iloc[-1])
            prev_close    = float(close.iloc[-2])
            current_open  = float(open_s.iloc[-1])
            prev_open     = float(open_s.iloc[-2])
            current_vol   = float(volume.iloc[-1])

            # Moving Averages
            sma_20 = ta.trend.sma_indicator(close, window=20)
            sma_50 = ta.trend.sma_indicator(close, window=50)
            sma_200 = ta.trend.sma_indicator(close, window=200)

            # RSI & MACD
            rsi = float(ta.momentum.rsi(close, window=14).iloc[-1])
            macd_obj = ta.trend.MACD(close)
            macd_hist = macd_obj.macd_diff()
            macd_cross = (float(macd_hist.iloc[-1]) > 0) and (float(macd_hist.iloc[-2]) <= 0)

            # ADX & ATR
            adx = float(ta.trend.ADXIndicator(high, low, close, window=14).adx().iloc[-1])
            atr = float(ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1])

            avg_vol_20d = float(volume.tail(20).mean())

            # Support / Resistance (using 20 days)
            support = float(low.rolling(window=20).min().iloc[-1])
            resistance = float(high.rolling(window=20).max().iloc[-1])

            strategy, raw_stop = determine_strategy(
                current_open, current_close, prev_open, prev_close,
                float(sma_20.iloc[-1]), float(sma_20.iloc[-2]), float(sma_50.iloc[-1]), float(sma_200.iloc[-1]),
                rsi, macd_cross, adx, atr, current_vol, avg_vol_20d, support, resistance
            )
            
            if not strategy:
                continue 

            entry, stop_loss, target = calculate_levels(current_close, raw_stop)
            
            if target > current_close * 1.5:
                target = current_close * 1.2

            hist['SMA_20'] = sma_20
            hist['SMA_50'] = sma_50
            hist['SMA_200'] = sma_200
            hist['Volume_SMA_20'] = ta.trend.sma_indicator(volume, window=20)
            hist['RSI_14'] = ta.momentum.rsi(close, window=14)
            
            macd_obj_full = ta.trend.MACD(close)
            hist['MACD'] = macd_obj_full.macd()
            hist['MACD_Signal'] = macd_obj_full.macd_signal()
            hist['MACD_Hist'] = macd_obj_full.macd_diff()
            
            clean_ticker = ticker.replace('.NS', '')

            results.append({
                'Ticker': clean_ticker,
                'Sector': sector_map.get(ticker, "Unknown"),
                'Strategy': strategy,
                'Entry': entry,
                'Stop Loss': stop_loss,
                'Target': target,
                'SMA 50': round(float(sma_50.iloc[-1]), 2),
                'ADX': round(adx, 2),
                'Vol Surge': round(current_vol / avg_vol_20d, 2) if avg_vol_20d > 0 else 1.0,
                'RSI': round(rsi, 2),
                'Support': support,
                'Resistance': resistance
            })
            
            historical_data_map[clean_ticker] = hist
            
        except Exception as e:
            continue

    return pd.DataFrame(results), historical_data_map

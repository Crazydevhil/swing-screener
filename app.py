import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import news_fetcher
from screener_logic import get_tickers, fetch_technicals_swing

# Page config
st.set_page_config(
    page_title="Screener | Indian Equity Swing",
    layout="wide",
    initial_sidebar_state="expanded",
)

FONT_UI = "Inter, Helvetica Neue, Arial, sans-serif"
FONT_DATA = "IBM Plex Mono, Consolas, monospace"
CHART_LOOKBACK = 120

CHART_THEME = {
    "paper": "#0f172a",
    "plot": "#1e293b",
    "grid": "#334155",
    "axis": "#475569",
    "text": "#f8fafc",
    "muted": "#94a3b8",
    "candle_up_line": "#10b981",
    "candle_up_fill": "rgba(16, 185, 129, 0.2)",
    "candle_down_line": "#f43f5e",
    "candle_down_fill": "rgba(244, 63, 94, 0.8)",
    "sma_20": "#94a3b8",
    "sma_50": "#3b82f6",
    "sma_200": "#f8fafc",
    "entry": "#3b82f6",
    "sl": "#f43f5e",
    "target": "#10b981",
    "support": "rgba(248, 250, 252, 0.05)",
    "resistance": "rgba(248, 250, 252, 0.05)",
    "volume": "#475569",
    "volume_sma": "#94a3b8",
    "rsi_line": "#3b82f6",
    "rsi_zone": "#1e293b",
    "macd_line": "#3b82f6",
    "macd_signal": "#fbbf24",
    "macd_hist_pos": "rgba(16, 185, 129, 0.4)",
    "macd_hist_neg": "rgba(244, 63, 94, 0.4)",
}


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {
            --ink: #f8fafc;
            --ink-2: #cbd5e1;
            --muted: #94a3b8;
            --line: #334155;
            --panel: #1e293b;
            --wash: #0f172a;
            --wash-2: #0f172a;
            --accent: #3b82f6;
            --accent-soft: rgba(59, 130, 246, 0.15);
            --accent-hover: #2563eb;
            --loss: #f43f5e;
            --gain: #10b981;
        }

        /* Base & Resets */
        .stApp { background: var(--wash); }

        .block-container {
            padding-top: 4rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        footer { visibility: hidden; height: 0; }
        header[data-testid="stHeader"] {
            background: rgba(15, 23, 42, 0.85) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--line);
        }

        /* Typography */
        h1, h2, h3, h4, p, label, .stMarkdown,
        .stSelectbox, .stButton, [data-testid="stMarkdownContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }

        code, [data-testid="stDataFrame"] td {
            font-family: 'IBM Plex Mono', monospace !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: var(--panel);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 2rem;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: var(--ink-2) !important;
        }
        [data-testid="stSidebar"] hr { border-color: var(--line); margin: 1.5rem 0; }

        /* Buttons & Interactive Elements */
        .stButton > button {
            border-radius: 6px;
            font-weight: 500;
            letter-spacing: 0.01em;
            padding: 0.6rem 1.2rem;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            background-color: var(--panel);
            border: 1px solid var(--line);
            color: var(--ink);
        }
        .stButton > button:hover {
            border-color: var(--accent);
            color: var(--accent);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .stButton > button:active {
            transform: translateY(0);
        }

        /* Top Navigation Bar */
        .top-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1.25rem 1.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .top-bar .brand {
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--ink) !important;
            margin: 0;
        }
        .top-bar .meta {
            font-size: 0.85rem;
            color: var(--muted) !important;
            margin: 0;
            font-weight: 500;
        }

        /* Page Intro */
        .page-intro {
            margin-bottom: 2rem;
        }
        .page-intro h1 {
            color: var(--ink) !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em;
            margin: 0 0 0.5rem 0 !important;
        }
        .page-intro p {
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.6;
            margin: 0;
            max-width: 800px;
        }

        /* Strategy Strip */
        .strat-strip {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        @media (max-width: 960px) { .strat-strip { grid-template-columns: 1fr; } }
        .strat-item {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .strat-item:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .strat-item .num {
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.15em;
            color: var(--accent);
            text-transform: uppercase;
            margin: 0 0 0.5rem 0;
        }
        .strat-item .name {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.01em;
        }
        .strat-item .desc {
            color: var(--muted);
            font-size: 0.85rem;
            line-height: 1.5;
            margin: 0;
        }

        /* Info Bar */
        .info-bar {
            background: var(--panel);
            border: 1px solid var(--line);
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 1rem 1.25rem;
            font-size: 0.85rem;
            color: var(--ink-2);
            margin-bottom: 2rem;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }

        /* Section Labels */
        .section-label {
            display: flex;
            align-items: baseline;
            gap: 0.75rem;
            margin: 2.5rem 0 1rem 0;
        }
        .section-label h2 {
            color: var(--ink) !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin: 0 !important;
        }
        .section-label span {
            color: var(--muted);
            font-size: 0.8rem;
        }

        /* Trade Metrics Cards */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        @media (max-width: 1100px) { .metrics-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 640px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }
        .m-cell {
            background: var(--wash);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .m-cell:hover {
            border-color: var(--accent);
            transform: translateY(-1px);
        }
        .m-cell .k {
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
        }
        .m-cell .v {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--ink);
            margin-top: 0.25rem;
        }
        .m-cell.entry .v { color: var(--accent); }
        .m-cell.sl .v { color: var(--loss); }
        .m-cell.tgt .v { color: var(--gain); }

        /* Stock Setup Cards */
        .setup-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding-bottom: 1rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid var(--line);
        }
        .setup-card-header .ticker {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--ink);
            letter-spacing: -0.02em;
        }
        .setup-card-header .meta {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.85rem;
            color: var(--muted);
        }
        .setup-card-header .price {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--ink);
        }
        .pill {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            background: var(--accent-soft);
            color: var(--accent);
            margin-left: 0.5rem;
        }

        .scan-line {
            color: var(--muted);
            font-size: 0.9rem;
            padding: 0.5rem 0 1rem 0;
        }

        .stAlert { border-radius: 8px; border: 1px solid var(--line); }

        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line) !important;
            border-radius: 12px !important;
            background-color: var(--panel);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: var(--line) !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_site_header():
    st.markdown(
        """
        <div class="top-bar">
            <p class="brand">Pro Screener</p>
            <p class="meta">Indian Equities · Nifty 500 · NSE</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=300)
def render_nifty_live():
    try:
        import yfinance as yf
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="1y").dropna(subset=['Close'])
        if len(hist) >= 2:
            last = hist.iloc[-1]['Close']
            prev = hist.iloc[-2]['Close']
            pct = ((last - prev) / prev) * 100
            color = "#10b981" if pct >= 0 else "#f43f5e"
            fill_color = "rgba(16, 185, 129, 0.15)" if pct >= 0 else "rgba(244, 63, 94, 0.15)"
            sign = "+" if pct >= 0 else ""
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist['Close'], 
                mode='lines',
                fill='tozeroy',
                fillcolor=fill_color,
                line=dict(color=color, width=2.5),
                hoverinfo='skip'
            ))
            fig.update_layout(
                height=120, margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"**NIFTY 50**<br><span style='font-size:1.4rem;font-weight:700;'>{last:,.2f}</span><br><span style='color:{color};font-weight:600;'>{sign}{pct:.2f}%</span>", unsafe_allow_html=True)
            with col2:
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except:
        pass

def render_page_intro():
    st.markdown(
        """
        <div class="page-intro">
            <h1>Swing Equity Screener</h1>
            <p>
                Multi-strategy scan for Indian equities — trend pullbacks, momentum breakouts,
                and support reversals with ATR-based risk controls.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_strategy_strip():
    st.markdown(
        """
        <div class="strat-strip">
            <div class="strat-item">
                <p class="num">01 — Pullback</p>
                <p class="name">Trend Pullback</p>
                <p class="desc">Buy dips in uptrends confirmed above 50 &amp; 200 SMA.</p>
            </div>
            <div class="strat-item">
                <p class="num">02 — Breakout</p>
                <p class="name">Momentum Breakout</p>
                <p class="desc">Volume expansion through resistance with MACD confirmation.</p>
            </div>
            <div class="strat-item">
                <p class="num">03 — Reversal</p>
                <p class="name">Support Reversal</p>
                <p class="desc">Oversold bounce at structural support with reversal candle.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("View exact selection logic for each strategy", expanded=False):
        st.markdown(
            """
            **Strategy 1: Trend Pullback**
            - SMA 50 > SMA 200 (Uptrend confirmed)
            - ADX (14) > 20 (Strong trend presence)
            - RSI (14) between 35 and 60 (Genuine pullback, not panic selling)
            - Price is within 15% of the recent 20-day support low
            - Conviction Candle: Today's Close > Open

            **Strategy 2: Momentum Breakout**
            - Volume > 1.5 × 20-day Volume SMA (Volume Surge)
            - RSI (14) > 55 (Strong momentum)
            - MACD Histogram crossed zero OR Price crossed above 20 SMA

            **Strategy 3: Support Reversal**
            - RSI (14) < 45 (Oversold condition)
            - Bullish Engulfing Candlestick pattern today
            - Price is within 5% of the recent 20-day support low
            """
        )
    st.markdown(
        """
        <div class="info-bar" style="margin-top: 1rem;">
            Risk model: Strict 1:3 Risk-Reward ratio. Target = Entry + 3x Risk.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_controls():
    st.sidebar.markdown(
        """
        <p style="font-size:1.25rem;font-weight:800;color:var(--ink);margin:0 0 0.2rem 0;letter-spacing:-0.03em;">
        Pro Screener</p>
        <p style="font-size:0.78rem;color:var(--muted);margin:0 0 1.25rem 0;">
        Scan parameters</p>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_app_menu():
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p style="font-size:0.8rem;color:#9e9e9e;font-weight:600;margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:0.05em;">System</p>', unsafe_allow_html=True)
    if st.sidebar.button("Rerun App", use_container_width=True, help="Refresh the app"):
        st.rerun()
    if st.sidebar.button("Clear Cache", use_container_width=True, help="Clear cached market data"):
        st.cache_data.clear()
        st.session_state.clear()
        st.toast("Cache cleared", icon="✅")
        st.rerun()


@st.cache_data(ttl=86400)
def load_index_tickers(index_key):
    return get_tickers(index_key)


def render_setup_header(stock):
    st.markdown(
        f"""
        <div class="setup-card-header">
            <div>
                <span class="ticker">{stock['Ticker']}</span>
                <span class="pill">{stock['Strategy']}</span>
            </div>
            <div class="price">₹{stock['Close']:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, subtitle=""):
    sub = f"<span>{subtitle}</span>" if subtitle else ""
    st.markdown(
        f'<div class="section-label"><h2>{title}</h2>{sub}</div>',
        unsafe_allow_html=True,
    )


def render_stock_metrics(stock):
    close = stock["Close"]
    sl = stock["Stop Loss"]
    target = stock["Target"]
    risk = close - sl
    reward = target - close
    rr = f"{reward / risk:.1f}:1" if risk > 0 else "—"

    st.markdown(
        f"""
        <div class="metrics-grid" style="grid-template-columns: repeat(7, 1fr);">
            <div class="m-cell entry"><div class="k">Entry</div><div class="v">₹{close:.2f}</div></div>
            <div class="m-cell sl"><div class="k">Stop</div><div class="v">₹{sl:.2f}</div></div>
            <div class="m-cell tgt"><div class="k">Target</div><div class="v">₹{target:.2f}</div></div>
            <div class="m-cell"><div class="k">R:R</div><div class="v">{rr}</div></div>
            <div class="m-cell"><div class="k">RSI</div><div class="v">{stock.get('RSI', 0):.1f}</div></div>
            <div class="m-cell"><div class="k">Vol Surge</div><div class="v">{stock.get('Vol Surge', 1.0):.1f}x</div></div>
            <div class="m-cell"><div class="k">Sector</div><div class="v" style="font-size:0.72rem;">{stock['Sector']}</div></div>
        </div>
        <div class="metrics-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 1rem;">
            <div class="m-cell"><div class="k">Support</div><div class="v">₹{stock['Support']:.2f}</div></div>
            <div class="m-cell"><div class="k">Resistance</div><div class="v">₹{stock['Resistance']:.2f}</div></div>
            <div class="m-cell"><div class="k">Setup</div><div class="v" style="font-size:0.72rem;">{stock['Strategy']}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_news_panel(ticker, ticker_full):
    """Native Streamlit rendering — reliable links and formatting."""
    news_items = news_fetcher.get_latest_news(ticker_full, count=5)

    with st.container(border=True):
        st.markdown(f"**Headlines** · `{ticker}`")
        st.caption("Source: Yahoo Finance")

        if not news_items:
            st.info("No recent headlines available for this symbol.")
            return

        for i, item in enumerate(news_items):
            title = item.get("title", "Untitled")
            publisher = item.get("publisher", "Unknown")
            published = item.get("published", "")
            link = (item.get("link") or "").strip()

            meta = publisher + (f" · {published}" if published else "")

            if link and link != "#":
                st.markdown(f"[{title}]({link})")
            else:
                st.markdown(f"**{title}**")

            st.caption(meta)

            if i < len(news_items) - 1:
                st.divider()


def style_results_table(results_df):
    return (
        results_df.style.format(
            {"Close": "₹{:.2f}", "Stop Loss": "₹{:.2f}", "Target": "₹{:.2f}", "RSI": "{:.1f}"}
        )
        .set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#f9f9f9"),
                        ("color", "#444444"),
                        ("font-weight", "600"),
                        ("font-size", "0.8rem"),
                        ("text-transform", "uppercase"),
                        ("letter-spacing", "0.05em"),
                        ("padding", "12px 14px"),
                        ("border-bottom", "2px solid #eeeeee"),
                    ],
                },
                {
                    "selector": "tbody td",
                    "props": [
                        ("padding", "10px 14px"),
                        ("font-size", "0.85rem"),
                        ("border-bottom", "1px solid #eeeeee"),
                        ("font-family", "'IBM Plex Mono', monospace"),
                        ("color", "#444444"),
                    ],
                },
                {
                    "selector": "tbody tr:nth-child(even)",
                    "props": [("background-color", "#ffffff")],
                },
                {
                    "selector": "tbody tr:hover",
                    "props": [("background-color", "#f2f2f2")],
                },
            ]
        )
        .hide(axis="index")
    )


def _style_chart_axes(fig, rows, *, show_x_labels_on_last_only=True):
    t = CHART_THEME
    axis_font = dict(family=FONT_UI, size=10, color=t["muted"])
    tick_font = dict(family=FONT_DATA, size=9, color=t["text"])

    for row in range(1, rows + 1):
        fig.update_yaxes(
            row=row,
            col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor=t["grid"],
            zeroline=False,
            linecolor=t["axis"],
            linewidth=1,
            tickfont=tick_font,
            title_font=axis_font,
            title_standoff=6,
        )
        fig.update_xaxes(
            row=row,
            col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor=t["grid"],
            zeroline=False,
            linecolor=t["axis"],
            linewidth=1,
            tickfont=tick_font,
            showticklabels=not show_x_labels_on_last_only or row == rows,
        )


def _add_trade_level(fig, y_val, color, label, row=1):
    yref = {1: "y", 2: "y2", 3: "y3", 4: "y4"}.get(row, "y")

    fig.add_hline(
        y=y_val,
        line=dict(color=color, width=1, dash="dot"),
        row=row,
        col=1,
    )
    fig.add_annotation(
        xref="paper",
        x=1.01,
        y=y_val,
        yref=yref,
        text=f"{label}  ₹{y_val:,.2f}",
        showarrow=False,
        xanchor="left",
        font=dict(family=FONT_DATA, size=9, color=color),
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor=color,
        borderwidth=1,
        borderpad=4,
    )


def create_chart(df, ticker, buy_price, sl, target, support=None, resistance=None):
    """Multi-panel institutional chart: price, volume, RSI, MACD."""
    t = CHART_THEME
    d = df.dropna(subset=['Close']).tail(CHART_LOOKBACK).copy()
    last_close = d["Close"].iloc[-1]
    pct_chg = ((last_close - d["Close"].iloc[-2]) / d["Close"].iloc[-2] * 100) if len(d) > 1 else 0

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        row_heights=[0.48, 0.14, 0.19, 0.19],
        subplot_titles=(
            f"{ticker}  ·  ₹{last_close:,.2f}  ({pct_chg:+.2f}%)",
            "Volume",
            "RSI (14)",
            "MACD",
        ),
        specs=[[{"secondary_y": False}]] * 4,
    )

    # --- Price panel ---
    fig.add_trace(
        go.Candlestick(
            x=d.index,
            open=d["Open"],
            high=d["High"],
            low=d["Low"],
            close=d["Close"],
            name="OHLC",
            increasing_line_color=t["candle_up_line"],
            increasing_fillcolor=t["candle_up_fill"],
            decreasing_line_color=t["candle_down_line"],
            decreasing_fillcolor=t["candle_down_fill"],
        ),
        row=1,
        col=1,
    )

    ma_specs = [
        ("SMA_20", t["sma_20"], "20 SMA", "dot"),
        ("SMA_50", t["sma_50"], "50 SMA", "solid"),
        ("SMA_200", t["sma_200"], "200 SMA", "solid"),
    ]
    for col, color, name, dash in ma_specs:
        if col in d.columns and d[col].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=d.index,
                    y=d[col],
                    name=name,
                    line=dict(color=color, width=1 if col == "SMA_20" else 1.25, dash=dash),
                    opacity=0.9,
                ),
                row=1,
                col=1,
            )

    if support is not None and resistance is not None:
        fig.add_hrect(
            y0=support * 0.995,
            y1=support * 1.005,
            fillcolor=t["support"],
            line_width=0,
            row=1,
            col=1,
        )
        fig.add_hrect(
            y0=resistance * 0.995,
            y1=resistance * 1.005,
            fillcolor=t["resistance"],
            line_width=0,
            row=1,
            col=1,
        )

    _add_trade_level(fig, buy_price, t["entry"], "Entry", row=1)
    _add_trade_level(fig, sl, t["sl"], "Stop", row=1)
    _add_trade_level(fig, target, t["target"], "Target", row=1)

    # --- Volume ---
    fig.add_trace(
        go.Bar(
            x=d.index,
            y=d["Volume"],
            name="Volume",
            marker=dict(color=t["volume"], line=dict(width=0)),
            opacity=0.85,
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    if "Volume_SMA_20" in d.columns:
        fig.add_trace(
            go.Scatter(
                x=d.index,
                y=d["Volume_SMA_20"],
                name="Vol SMA 20",
                line=dict(color=t["volume_sma"], width=1),
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    # --- RSI ---
    if "RSI_14" in d.columns:
        fig.add_trace(
            go.Scatter(
                x=d.index,
                y=d["RSI_14"],
                name="RSI (14)",
                line=dict(color=t["rsi_line"], width=1.25),
                showlegend=False,
            ),
            row=3,
            col=1,
        )
        fig.add_hrect(y0=70, y1=100, fillcolor=t["rsi_zone"], line_width=0, row=3, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor=t["rsi_zone"], line_width=0, row=3, col=1)
        for level in (30, 50, 70):
            fig.add_hline(y=level, line=dict(color=t["axis"], width=1, dash="dot"), row=3, col=1)

    # --- MACD ---
    if "MACD_Hist" in d.columns:
        hist_colors = [
            t["macd_hist_pos"] if v >= 0 else t["macd_hist_neg"]
            for v in d["MACD_Hist"].fillna(0)
        ]
        fig.add_trace(
            go.Bar(
                x=d.index,
                y=d["MACD_Hist"],
                name="MACD Hist",
                marker_color=hist_colors,
                showlegend=False,
            ),
            row=4,
            col=1,
        )
    if "MACD" in d.columns:
        fig.add_trace(
            go.Scatter(
                x=d.index,
                y=d["MACD"],
                name="MACD",
                line=dict(color=t["macd_line"], width=1.1),
                showlegend=False,
            ),
            row=4,
            col=1,
        )
    if "MACD_Signal" in d.columns:
        fig.add_trace(
            go.Scatter(
                x=d.index,
                y=d["MACD_Signal"],
                name="Signal",
                line=dict(color=t["macd_signal"], width=1),
                showlegend=False,
            ),
            row=4,
            col=1,
        )

    fig.update_layout(
        height=840,
        paper_bgcolor=t["paper"],
        plot_bgcolor=t["plot"],
        font=dict(family=FONT_UI, color=t["text"], size=11),
        margin=dict(l=52, r=100, t=80, b=48),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=t["plot"],
            bordercolor=t["grid"],
            font=dict(family="Inter", size=13, color=t["text"]),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family=FONT_UI, size=9),
            bgcolor=t["paper"],
            bordercolor=t["axis"],
            borderwidth=1,
        ),
        title="",
        xaxis_rangeslider_visible=False,
    )

    for i, ann in enumerate(fig.layout.annotations):
        if i < 4:
            ann.font = dict(family=FONT_UI, size=11 if i > 0 else 12, color=t["text"])
            ann.xanchor = "left"
            ann.x = 0.01

    fig.update_yaxes(title_text="Price (₹)", row=1, col=1, tickformat=",.0f")
    fig.update_yaxes(title_text="Vol", row=2, col=1, tickformat=".2s")
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    _style_chart_axes(fig, 4)
    fig.update_xaxes(
        rangebreaks=[dict(bounds=["sat", "mon"])],
        title_text="Date",
        title_standoff=8,
        row=4,
        col=1,
    )
    fig.update_xaxes(showticklabels=True, row=4, col=1)

    for row in (1, 2, 3):
        fig.update_xaxes(showticklabels=False, row=row, col=1)

    return fig


def main():
    inject_custom_css()
    render_sidebar_controls()

    render_site_header()
    render_nifty_live()
    render_page_intro()
    render_strategy_strip()

    st.sidebar.markdown("### Sector Filtering")
    index_choice = st.sidebar.selectbox("Select Index", ["Nifty 50", "Nifty 500"])
    index_key = "nifty50" if index_choice == "Nifty 50" else "nifty500"
    
    tickers_list, sector_map = load_index_tickers(index_key)
    all_sectors = sorted(list(set(sector_map.values())))
    selected_sectors = st.sidebar.multiselect("Select Sectors (Leave empty for all)", all_sectors, default=[])

    st.sidebar.markdown("---")
    st.sidebar.markdown('<p style="font-size:0.8rem;color:#9e9e9e;font-weight:600;margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:0.05em;">Actions</p>', unsafe_allow_html=True)
    run_clicked = st.sidebar.button("Run Screener", type="primary", use_container_width=True)
    render_sidebar_app_menu()

    if run_clicked:
        st.markdown(
            f'<p class="scan-line">Scanning {index_choice} with Ultra-Strict filters — please wait.</p>',
            unsafe_allow_html=True,
        )

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total, ticker):
            progress = int((current / total) * 100)
            progress_bar.progress(progress)
            status_text.markdown(
                f'<p class="scan-line">Processing <strong>{ticker}</strong> · {current} / {total}</p>',
                unsafe_allow_html=True,
            )

        df_results, historical_data_map = fetch_technicals_swing(
            tickers_list, 
            sector_map, 
            selected_sectors=selected_sectors, 
            progress_callback=update_progress
        )

        progress_bar.empty()
        status_text.empty()
        
        st.session_state["has_scanned"] = True
        st.session_state["scan_results"] = df_results
        st.session_state["historical_data_map"] = historical_data_map

    if st.session_state.get("has_scanned", False):
        df_results = st.session_state.get("scan_results", pd.DataFrame())
        historical_data_map = st.session_state.get("historical_data_map", {})
        passed_stocks = df_results.to_dict('records') if not df_results.empty else []

        if passed_stocks:
            st.success(
                f"Scan complete — {len(passed_stocks)} pristine setup{'s' if len(passed_stocks) != 1 else ''} found."
            )

            section_heading("Screening Results", f"{len(passed_stocks)} matches")
            cols = ["Ticker", "Sector", "Strategy", "Entry", "Stop Loss", "Target", "Vol Surge"]
            results_df = df_results[cols].rename(columns={'Entry': 'Close'})
            st.dataframe(style_results_table(results_df), width="stretch", hide_index=True)

            section_heading("Trade Analysis", "Charts & headlines")

            for stock in passed_stocks:
                ticker_key = stock['Ticker']
                stock['Close'] = stock['Entry'] # Alias entry to close for UI cards
                
                with st.container(border=True):
                    render_setup_header(stock)
                    render_stock_metrics(stock)
                    with st.expander("View Chart & Headlines", expanded=False):
                        chart_col, news_col = st.columns([2.2, 1], gap="medium")

                        with chart_col:
                            df = historical_data_map.get(ticker_key)
                            if df is not None:
                                st.plotly_chart(
                                    create_chart(
                                        df,
                                        stock["Ticker"],
                                        stock["Entry"],
                                        stock["Stop Loss"],
                                        stock["Target"],
                                        support=stock.get("Support"),
                                        resistance=stock.get("Resistance"),
                                    ),
                                    use_container_width=True
                                )

                        with news_col:
                            render_news_panel(stock["Ticker"], f"{stock['Ticker']}.NS")
        else:
            st.warning(
                "No symbols matched today's ultra-strict criteria. Cash is a valid position!"
            )


if __name__ == "__main__":
    main()

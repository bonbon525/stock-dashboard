import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #30363d !important;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: #c9d1d9 !important; font-size: 1.2rem !important; font-weight: 600 !important; }
[data-testid="stDataFrame"] { border: 1px solid #30363d !important; border-radius: 6px; }
h1 { color: #ffffff !important; }
h2, h3 { color: #e6edf3 !important; }
hr { border-color: #30363d !important; }
.card-gainer {
    background: #0d2818; border: 1px solid #238636;
    border-radius: 8px; padding: 16px 20px; margin-top: 8px;
}
.card-loser {
    background: #2d1419; border: 1px solid #f85149;
    border-radius: 8px; padding: 16px 20px; margin-top: 8px;
}
.card-price { font-size: 2rem; font-weight: 700; color: #ffffff; margin: 4px 0; }
.badge-up   { background:#1a3d25; color:#3fb950; padding:3px 10px; border-radius:4px; font-size:0.85rem; font-weight:600; }
.badge-down { background:#3d1519; color:#f85149; padding:3px 10px; border-radius:4px; font-size:0.85rem; font-weight:600; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Stock universe ────────────────────────────────────────────────────────────
STOCKS = {
    # Semiconductors
    "NVDA":  ("NVIDIA",                      "Semiconductors"),
    "AMD":   ("Advanced Micro Devices",      "Semiconductors"),
    "INTC":  ("Intel",                       "Semiconductors"),
    "QCOM":  ("Qualcomm",                    "Semiconductors"),
    "AVGO":  ("Broadcom",                    "Semiconductors"),
    "TXN":   ("Texas Instruments",           "Semiconductors"),
    "AMAT":  ("Applied Materials",           "Semiconductors"),
    "LRCX":  ("Lam Research",               "Semiconductors"),
    "KLAC":  ("KLA Corporation",             "Semiconductors"),
    "MU":    ("Micron Technology",           "Semiconductors"),
    "MRVL":  ("Marvell Technology",          "Semiconductors"),
    "ADI":   ("Analog Devices",              "Semiconductors"),
    "MCHP":  ("Microchip Tech",              "Semiconductors"),
    "ON":    ("ON Semiconductor",            "Semiconductors"),
    "MPWR":  ("Monolithic Power",            "Semiconductors"),
    "SWKS":  ("Skyworks",                    "Semiconductors"),
    "QRVO":  ("Qorvo",                       "Semiconductors"),
    "LSCC":  ("Lattice Semi",               "Semiconductors"),
    "ENTG":  ("Entegris",                    "Semiconductors"),
    "TER":   ("Teradyne",                    "Semiconductors"),
    "ASML":  ("ASML",                        "Semiconductors"),
    "TSM":   ("Taiwan Semiconductor (TSMC)", "Semiconductors"),
    # Big Tech
    "AAPL":  ("Apple",                       "Big Tech"),
    "MSFT":  ("Microsoft",                   "Big Tech"),
    "GOOGL": ("Alphabet",                    "Big Tech"),
    "META":  ("Meta Platforms",              "Big Tech"),
    "AMZN":  ("Amazon",                      "Big Tech"),
    "TSLA":  ("Tesla",                       "Big Tech"),
    "IBM":   ("IBM",                         "Big Tech"),
    "ORCL":  ("Oracle",                      "Big Tech"),
}


def fmt_mktcap(v):
    if v is None:   return "—"
    if v >= 1e12:   return f"${v/1e12:.2f}T"
    if v >= 1e9:    return f"${v/1e9:.2f}B"
    return f"${v/1e6:.1f}M"


@st.cache_data(ttl=300)
def fetch_overview():
    tickers = list(STOCKS.keys())
    raw = yf.download(tickers, period="5d", auto_adjust=True, progress=False)
    close = raw["Close"]
    rows = []
    for ticker in tickers:
        if ticker not in close.columns:
            continue
        s = close[ticker].dropna()
        if len(s) < 2:
            continue
        price = float(s.iloc[-1])
        prev  = float(s.iloc[-2])
        chg   = price - prev
        rows.append({
            "Ticker":   ticker,
            "Company":  STOCKS[ticker][0],
            "Sector":   STOCKS[ticker][1],
            "Price":    round(price, 2),
            "Change":   round(chg, 2),
            "Change %": round(chg / prev * 100, 2),
        })
    df = pd.DataFrame(rows).set_index("Ticker")
    return df.sort_values("Change %", ascending=False)


@st.cache_data(ttl=300)
def fetch_detail(ticker: str, start, end, sma_periods: tuple):
    t   = yf.Ticker(ticker)
    df  = t.history(start=str(start), end=str(end), auto_adjust=True)
    if df.index.tzinfo is not None:
        df.index = df.index.tz_convert(None)

    for p in sma_periods:
        df[f"SMA{p}"] = df["Close"].rolling(p).mean()

    mkt_cap, pe, long_name = None, None, ticker
    try:
        fi = t.fast_info
        mkt_cap = getattr(fi, "market_cap", None)
    except Exception:
        pass
    try:
        info = t.info
        pe        = info.get("trailingPE")
        long_name = info.get("longName", ticker)
    except Exception:
        pass

    return df, mkt_cap, pe, long_name


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Chart settings")
start_date = st.sidebar.date_input("Start date", date.today() - timedelta(days=365))
end_date   = st.sidebar.date_input("End date",   date.today())
sma20  = st.sidebar.checkbox("20-day SMA",  value=True)
sma50  = st.sidebar.checkbox("50-day SMA",  value=True)
sma200 = st.sidebar.checkbox("200-day SMA", value=False)
st.sidebar.caption("💡 Many traders watch the 50-day and 200-day lines for the overall trend.")

sma_periods = tuple(p for p, on in [(20, sma20), (50, sma50), (200, sma200)] if on)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📈 Stock Dashboard")
st.markdown(
    "Track 30 well-known semiconductor & tech companies, then dive into any one for a detailed chart. "
    "New here? Look for the 💡 tips and check the glossary below the table."
)

# ── Sector filter ─────────────────────────────────────────────────────────────
sector_filter = st.radio("Filter by sector", ["All", "Semiconductors", "Big Tech"], horizontal=True)

# ── Overview table ────────────────────────────────────────────────────────────
with st.spinner("Loading market data…"):
    df = fetch_overview()

if sector_filter != "All":
    df = df[df["Sector"] == sector_filter]

def _color_num(val):
    if val > 0: return "color: #3fb950; font-weight: 600"
    if val < 0: return "color: #f85149; font-weight: 600"
    return ""

styled = (
    df[["Company", "Sector", "Price", "Change", "Change %"]]
    .style
    .map(_color_num, subset=["Change", "Change %"])
    .format({"Price": "${:.2f}", "Change": "{:+.2f}", "Change %": "{:+.2f}%"})
    .set_properties(**{"background-color": "#161b22", "color": "#c9d1d9", "border-color": "#30363d"})
)

st.dataframe(styled, use_container_width=True, height=500)
st.caption("💡 Sorted by today's biggest gainers first. Green = up today, red = down today.")

# ── Top gainer / loser cards ──────────────────────────────────────────────────
gainer = df.iloc[0]
loser  = df.iloc[-1]

col_g, col_l = st.columns(2)
with col_g:
    badge = "badge-up" if gainer["Change %"] >= 0 else "badge-down"
    arrow = "↑" if gainer["Change %"] >= 0 else "↓"
    st.markdown(
        f'<div class="card-gainer">'
        f'<div style="font-size:.85rem;color:#8b949e">🚀 Top gainer — {gainer["Company"]}</div>'
        f'<div class="card-price">${gainer["Price"]:.2f}</div>'
        f'<span class="{badge}">{arrow} {gainer["Change %"]:+.2f}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
with col_l:
    badge = "badge-up" if loser["Change %"] >= 0 else "badge-down"
    arrow = "↑" if loser["Change %"] >= 0 else "↓"
    st.markdown(
        f'<div class="card-loser">'
        f'<div style="font-size:.85rem;color:#8b949e">📉 Top loser — {loser["Company"]}</div>'
        f'<div class="card-price">${loser["Price"]:.2f}</div>'
        f'<span class="{badge}">{arrow} {loser["Change %"]:+.2f}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Glossary ──────────────────────────────────────────────────────────────────
with st.expander("📚 New to investing? Key terms explained"):
    st.markdown("""
- **Ticker**: the short code a stock trades under, e.g. `AAPL` is Apple.
- **Price**: the most recent traded price for one share.
- **Change %**: how much the price moved since the previous close — the main "is it up or down" number.
- **Market Cap**: share price × total shares outstanding — a rough measure of how big the company is.
- **P/E Ratio**: price ÷ earnings per share. Higher usually means investors expect more future growth.
- **Volume**: number of shares traded. Big spikes often line up with earnings reports or big news.
- **SMA (Simple Moving Average)**: the average closing price over the last N days — smooths out daily noise to reveal the trend.
- **Candlestick chart**: each bar is one trading day — green means it closed higher than it opened, red means lower.
""")

st.divider()

# ── Detail section ────────────────────────────────────────────────────────────
st.markdown("## 🔎 Explore a company in detail")

watchlist_opts = [f"{t} — {STOCKS[t][0]}" for t in STOCKS]

col_pick, col_type = st.columns(2)
with col_pick:
    st.markdown("**Pick from your watchlist**")
    picked = st.selectbox("watchlist", watchlist_opts, label_visibility="collapsed")
    picked_ticker = picked.split(" — ")[0]
with col_type:
    st.markdown("**...or type any other ticker**")
    custom = st.text_input("custom", placeholder="e.g. NVDA, TSLA", label_visibility="collapsed").strip().upper()

detail_ticker = custom if custom else picked_ticker

with st.spinner(f"Loading {detail_ticker}…"):
    try:
        hist, mkt_cap, pe, long_name = fetch_detail(detail_ticker, start_date, end_date, sma_periods)
    except Exception as e:
        st.error(f"Could not load data for **{detail_ticker}**: {e}")
        st.stop()

if hist.empty:
    st.warning(f"No data found for **{detail_ticker}** in the selected date range.")
    st.stop()

last_close  = float(hist["Close"].iloc[-1])
prev_close  = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_close
day_chg     = last_close - prev_close
day_chg_pct = day_chg / prev_close * 100
period_high = float(hist["High"].max())
period_low  = float(hist["Low"].min())
avg_vol     = float(hist["Volume"].mean())

st.markdown(f"## {long_name} ({detail_ticker})")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Last Close",  f"${last_close:.2f}", f"{day_chg:+.2f} ({day_chg_pct:+.2f}%)")
k2.metric("Period High", f"${period_high:.2f}")
k3.metric("Period Low",  f"${period_low:.2f}")
k4.metric("Avg Volume",  f"{avg_vol/1e6:.1f}M" if avg_vol >= 1e6 else f"{avg_vol:,.0f}")
k5.metric("Market Cap",  fmt_mktcap(mkt_cap))
k6.metric("P/E Ratio",   f"{pe:.1f}" if pe else "—")

# ── Candlestick chart ─────────────────────────────────────────────────────────
SMA_COLORS = {20: "#2196f3", 50: "#ff9800", 200: "#e91e63"}

_base_layout = dict(
    paper_bgcolor="#161b22",
    plot_bgcolor="#0d1117",
    font=dict(color="#8b949e", size=11),
    legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
    margin=dict(l=60, r=20, t=20, b=40),
    hovermode="x unified",
)

fig_candle = go.Figure()
fig_candle.add_trace(go.Candlestick(
    x=hist.index,
    open=hist["Open"], high=hist["High"],
    low=hist["Low"],   close=hist["Close"],
    name=detail_ticker,
    increasing_line_color="#3fb950", increasing_fillcolor="#3fb950",
    decreasing_line_color="#f85149", decreasing_fillcolor="#f85149",
))
for p in sma_periods:
    col_name = f"SMA{p}"
    if col_name in hist.columns:
        fig_candle.add_trace(go.Scatter(
            x=hist.index, y=hist[col_name],
            name=f"{p}-day SMA",
            line=dict(color=SMA_COLORS.get(p, "#ffffff"), width=1.5),
            hovertemplate=f"SMA{p}: %{{y:.2f}}<extra></extra>",
        ))
fig_candle.update_layout(
    **_base_layout,
    xaxis=dict(gridcolor="#30363d", rangeslider=dict(visible=False), showgrid=True),
    yaxis=dict(gridcolor="#30363d", showgrid=True),
    height=420,
)
st.plotly_chart(fig_candle, use_container_width=True)
st.caption("💡 Each candle is one trading day. Green = closed higher than it opened; red = closed lower.")

# ── Volume chart ──────────────────────────────────────────────────────────────
vol_colors = [
    "#3fb950" if c >= o else "#f85149"
    for c, o in zip(hist["Close"], hist["Open"])
]
fig_vol = go.Figure(go.Bar(
    x=hist.index, y=hist["Volume"],
    marker_color=vol_colors,
    marker_line_width=0,
    showlegend=False,
))
fig_vol.update_layout(
    **_base_layout,
    xaxis=dict(gridcolor="#30363d", showgrid=True),
    yaxis=dict(gridcolor="#30363d", showgrid=True),
    height=220,
)
st.plotly_chart(fig_vol, use_container_width=True)
st.caption("💡 Volume spikes often line up with earnings reports or big news.")

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("Raw data"):
    show_cols = ["Close", "High", "Low", "Open", "Volume"] + [
        f"SMA{p}" for p in sma_periods if f"SMA{p}" in hist.columns
    ]
    raw = hist[show_cols].sort_index(ascending=False).round(2)
    st.dataframe(raw, use_container_width=True)
    csv = raw.reset_index().to_csv(index=False)
    st.download_button("Download CSV", csv, f"{detail_ticker}_data.csv", "text/csv")

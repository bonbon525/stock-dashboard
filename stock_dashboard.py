import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="Stock Intelligence", page_icon="📈", layout="wide")

# ── Global style ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Page background */
  .stApp { background-color: #0e1117; }

  /* Bigger base text */
  p, li, .stMarkdown { font-size: 1.05rem !important; color: #e0e0e0; }

  /* Section headers */
  h1 { font-size: 2.4rem !important; font-weight: 800 !important; color: #ffffff !important; }
  h2 { font-size: 1.8rem !important; font-weight: 700 !important; color: #ffffff !important; }
  h3 { font-size: 1.35rem !important; font-weight: 700 !important; color: #ffffff !important; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #1c2130;
    border-radius: 12px;
    padding: 18px 20px !important;
    border: 1px solid #2a3040;
  }
  [data-testid="metric-container"] label {
    font-size: 0.85rem !important;
    color: #8892a4 !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
  }
  [data-testid="stMetricDelta"] { font-size: 1rem !important; font-weight: 600 !important; }

  /* Signal badges */
  .badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .badge-strong-buy  { background:#0d3d2b; color:#22c55e; border:1px solid #22c55e; }
  .badge-buy         { background:#0f2a1a; color:#4ade80; border:1px solid #4ade80; }
  .badge-hold        { background:#1e2a14; color:#a3e635; border:1px solid #a3e635; }
  .badge-watch       { background:#2a1f0a; color:#fb923c; border:1px solid #fb923c; }
  .badge-avoid       { background:#2a0f0f; color:#f87171; border:1px solid #f87171; }

  /* Top-pick cards */
  .pick-card {
    background: linear-gradient(135deg, #1c2130 0%, #1a2540 100%);
    border-radius: 16px;
    padding: 22px 24px;
    border: 1px solid #2a3a5c;
    margin-bottom: 8px;
  }
  .pick-ticker  { font-size: 1.5rem; font-weight: 800; color: #60a5fa; }
  .pick-name    { font-size: 0.85rem; color: #8892a4; margin-top: 2px; }
  .pick-price   { font-size: 2rem; font-weight: 800; color: #ffffff; margin-top: 10px; }
  .pick-change  { font-size: 1rem; font-weight: 700; margin-top: 2px; }
  .up   { color: #22c55e; }
  .down { color: #f87171; }

  /* Divider */
  hr { border-color: #2a3040 !important; }

  /* Dataframe */
  .stDataFrame { border-radius: 12px; overflow: hidden; }

  /* Radio + selectbox labels */
  .stRadio label, .stSelectbox label { font-size: 1rem !important; font-weight: 600 !important; color: #c0c8d8 !important; }

  /* Sidebar */
  [data-testid="stSidebar"] { background-color: #131720 !important; border-right: 1px solid #2a3040; }
  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] label { color: #c0c8d8 !important; }

  /* Expander */
  [data-testid="stExpander"] { background: #1c2130 !important; border-radius: 12px !important; border: 1px solid #2a3040 !important; }
</style>
""", unsafe_allow_html=True)

# ── Watchlist ─────────────────────────────────────────────────────────────────
WATCHLIST = [
    {"ticker": "NVDA",  "name": "NVIDIA",                       "sector": "Semiconductors"},
    {"ticker": "AMD",   "name": "Advanced Micro Devices",        "sector": "Semiconductors"},
    {"ticker": "INTC",  "name": "Intel",                         "sector": "Semiconductors"},
    {"ticker": "AVGO",  "name": "Broadcom",                      "sector": "Semiconductors"},
    {"ticker": "QCOM",  "name": "Qualcomm",                      "sector": "Semiconductors"},
    {"ticker": "TXN",   "name": "Texas Instruments",             "sector": "Semiconductors"},
    {"ticker": "MU",    "name": "Micron Technology",             "sector": "Semiconductors"},
    {"ticker": "ASML",  "name": "ASML Holding",                  "sector": "Semiconductors"},
    {"ticker": "AMAT",  "name": "Applied Materials",             "sector": "Semiconductors"},
    {"ticker": "LRCX",  "name": "Lam Research",                  "sector": "Semiconductors"},
    {"ticker": "KLAC",  "name": "KLA Corporation",               "sector": "Semiconductors"},
    {"ticker": "ON",    "name": "ON Semiconductor",              "sector": "Semiconductors"},
    {"ticker": "MRVL",  "name": "Marvell Technology",            "sector": "Semiconductors"},
    {"ticker": "ADI",   "name": "Analog Devices",                "sector": "Semiconductors"},
    {"ticker": "TSM",   "name": "TSMC",                          "sector": "Semiconductors"},
    {"ticker": "AAPL",  "name": "Apple",                         "sector": "Big Tech"},
    {"ticker": "MSFT",  "name": "Microsoft",                     "sector": "Big Tech"},
    {"ticker": "GOOGL", "name": "Alphabet (Google)",             "sector": "Big Tech"},
    {"ticker": "AMZN",  "name": "Amazon",                        "sector": "Big Tech"},
    {"ticker": "META",  "name": "Meta Platforms",                "sector": "Big Tech"},
    {"ticker": "TSLA",  "name": "Tesla",                         "sector": "Big Tech"},
    {"ticker": "NFLX",  "name": "Netflix",                       "sector": "Big Tech"},
    {"ticker": "ORCL",  "name": "Oracle",                        "sector": "Big Tech"},
    {"ticker": "CRM",   "name": "Salesforce",                    "sector": "Big Tech"},
    {"ticker": "ADBE",  "name": "Adobe",                         "sector": "Big Tech"},
    {"ticker": "CSCO",  "name": "Cisco",                         "sector": "Big Tech"},
    {"ticker": "IBM",   "name": "IBM",                           "sector": "Big Tech"},
    {"ticker": "UBER",  "name": "Uber Technologies",             "sector": "Big Tech"},
    {"ticker": "SHOP",  "name": "Shopify",                       "sector": "Big Tech"},
    {"ticker": "PLTR",  "name": "Palantir Technologies",         "sector": "Big Tech"},
]
NAME_BY_TICKER   = {c["ticker"]: c["name"]   for c in WATCHLIST}
SECTOR_BY_TICKER = {c["ticker"]: c["sector"] for c in WATCHLIST}
ALL_TICKERS      = [c["ticker"] for c in WATCHLIST]


# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def load_snapshot(tickers):
    hist = yf.download(tickers, period="30d", group_by="ticker", auto_adjust=True, threads=True, progress=False)
    rows = []
    for t in tickers:
        try:
            sub = hist[t] if isinstance(hist.columns, pd.MultiIndex) else hist
            closes  = sub["Close"].dropna()
            volumes = sub["Volume"].dropna()
            if len(closes) < 2:
                continue
            last   = float(closes.iloc[-1])
            prev   = float(closes.iloc[-2])
            vol    = float(volumes.iloc[-1])
            avg_vol = float(volumes.mean())
            change = last - prev
            pct    = (change / prev * 100) if prev else 0.0
            # 5-day momentum
            pct5 = ((last / float(closes.iloc[-6])) - 1) * 100 if len(closes) >= 6 else pct
            # SMA20
            sma20 = float(closes.rolling(20).mean().iloc[-1]) if len(closes) >= 20 else None
        except Exception:
            continue

        rows.append({
            "Ticker":       t,
            "Company":      NAME_BY_TICKER[t],
            "Sector":       SECTOR_BY_TICKER[t],
            "Price":        last,
            "Change":       change,
            "Change %":     pct,
            "5D Momentum":  pct5,
            "Volume":       vol,
            "Avg Volume":   avg_vol,
            "SMA20":        sma20,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_history(symbol, start, end):
    data = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


@st.cache_data(ttl=3600)
def load_info(symbol):
    try:
        return yf.Ticker(symbol).info
    except Exception:
        return {}


# ── Signal engine ─────────────────────────────────────────────────────────────
def compute_signal(row) -> tuple[str, str]:
    """Return (signal_label, css_class) based on momentum + trend."""
    m1  = row["Change %"]
    m5  = row["5D Momentum"]
    above_sma = (row["SMA20"] is not None) and (row["Price"] > row["SMA20"])
    vol_surge = row["Volume"] > row["Avg Volume"] * 1.3

    score = 0
    score += 3 if m5 > 5 else 2 if m5 > 2 else 1 if m5 > 0 else -1 if m5 > -3 else -2
    score += 2 if m1 > 1 else 1 if m1 > 0 else -1
    score += 2 if above_sma else -1
    score += 1 if vol_surge else 0

    if score >= 7:
        return "Strong Buy", "strong-buy"
    elif score >= 4:
        return "Buy", "buy"
    elif score >= 1:
        return "Hold", "hold"
    elif score >= -1:
        return "Watch", "watch"
    else:
        return "Avoid", "avoid"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📈 Stock Intelligence Dashboard")
st.markdown("<p style='color:#8892a4;font-size:1.05rem;margin-top:-10px'>Semiconductor & Big Tech — signals updated every 15 min</p>", unsafe_allow_html=True)

# ── Sector filter ─────────────────────────────────────────────────────────────
sector_choice = st.radio("", ["All", "Semiconductors", "Big Tech"], horizontal=True)
tickers_to_show = ALL_TICKERS if sector_choice == "All" else [c["ticker"] for c in WATCHLIST if c["sector"] == sector_choice]

with st.spinner("Loading market data..."):
    snapshot = load_snapshot(tickers_to_show)

if snapshot.empty:
    st.error("Couldn't load market data. Try again shortly.")
    st.stop()

snapshot[["Signal", "SignalClass"]] = snapshot.apply(
    lambda r: pd.Series(compute_signal(r)), axis=1
)
snapshot = snapshot.sort_values("5D Momentum", ascending=False).reset_index(drop=True)

# ── Top Picks ─────────────────────────────────────────────────────────────────
st.markdown("### 🎯 Top Picks Right Now")
top_picks = snapshot[snapshot["Signal"].isin(["Strong Buy", "Buy"])].head(3)

if top_picks.empty:
    st.info("No strong signals today — market may be mixed. See full table below.")
else:
    cols = st.columns(len(top_picks))
    for col, (_, row) in zip(cols, top_picks.iterrows()):
        sign  = "+" if row["Change"] >= 0 else ""
        cls   = "up" if row["Change"] >= 0 else "down"
        badge = f'<span class="badge badge-{row["SignalClass"]}">{row["Signal"]}</span>'
        col.markdown(f"""
<div class="pick-card">
  {badge}
  <div class="pick-ticker" style="margin-top:12px">{row["Ticker"]}</div>
  <div class="pick-name">{row["Company"]}</div>
  <div class="pick-price">${row["Price"]:,.2f}</div>
  <div class="pick-change {cls}">{sign}{row["Change %"]:.2f}% today &nbsp;·&nbsp; {sign}{row["5D Momentum"]:.1f}% 5D</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gainer / Loser KPIs ───────────────────────────────────────────────────────
gainer = snapshot.iloc[0]
loser  = snapshot.iloc[-1]
m1, m2 = st.columns(2)
m1.metric(f"🚀 Best momentum — {gainer['Ticker']}", f"${gainer['Price']:,.2f}", f"{gainer['5D Momentum']:+.2f}% (5D)")
m2.metric(f"📉 Worst momentum — {loser['Ticker']}",  f"${loser['Price']:,.2f}",  f"{loser['5D Momentum']:+.2f}% (5D)")

st.divider()

# ── Full watchlist table ───────────────────────────────────────────────────────
st.markdown("### 📊 Full Watchlist")

def badge_html(val, css_class):
    return f'<span class="badge badge-{css_class}">{val}</span>'

display = snapshot[["Ticker", "Company", "Sector", "Price", "Change %", "5D Momentum", "Volume", "Signal"]].copy()

def color_pct(val):
    c = "#22c55e" if val >= 0 else "#f87171"
    return f"color: {c}; font-weight: 700"

styled = (
    display.style
    .format({
        "Price":        "${:,.2f}",
        "Change %":     "{:+.2f}%",
        "5D Momentum":  "{:+.2f}%",
        "Volume":       "{:,.0f}",
    })
    .map(color_pct, subset=["Change %", "5D Momentum"])
    .set_properties(**{"font-size": "14px"})
)
st.dataframe(styled, hide_index=True, use_container_width=True, height=460)
st.caption("Sorted by 5-day momentum. Signal = composite of momentum, trend vs SMA20, and volume activity.")

# ── Momentum bar chart ────────────────────────────────────────────────────────
st.markdown("### 📉 5-Day Momentum Comparison")
bar_colors = ["#22c55e" if v >= 0 else "#f87171" for v in snapshot["5D Momentum"]]
fig_bar = go.Figure(go.Bar(
    x=snapshot["Ticker"],
    y=snapshot["5D Momentum"],
    marker_color=bar_colors,
    text=[f"{v:+.1f}%" for v in snapshot["5D Momentum"]],
    textposition="outside",
    textfont=dict(size=11, color="#c0c8d8"),
))
fig_bar.update_layout(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#c0c8d8", size=13),
    height=320,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(tickfont=dict(size=12), gridcolor="#1c2130"),
    yaxis=dict(gridcolor="#1c2130", ticksuffix="%"),
    showlegend=False,
)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── Deep-dive ─────────────────────────────────────────────────────────────────
st.markdown("### 🔎 Company Deep Dive")

col_a, col_b = st.columns([2, 1])
with col_a:
    options  = snapshot["Ticker"].tolist()
    selected = st.selectbox("Pick a stock", options, format_func=lambda t: f"{t} — {NAME_BY_TICKER.get(t, t)}")
with col_b:
    custom_ticker = st.text_input("...or type any ticker", value="").strip().upper()

ticker = custom_ticker if custom_ticker else selected

with st.sidebar:
    st.markdown("## Chart settings")
    end_default   = date.today()
    start_default = end_default - timedelta(days=365)
    start_date = st.date_input("Start date", value=start_default)
    end_date   = st.date_input("End date",   value=end_default)
    show_sma20  = st.checkbox("20-day SMA",  value=True)
    show_sma50  = st.checkbox("50-day SMA",  value=True)
    show_sma200 = st.checkbox("200-day SMA", value=False)
    st.caption("50-day & 200-day lines show the long-term trend direction.")

if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

data = load_history(ticker, start_date, end_date)
if data.empty:
    st.error(f"No data for '{ticker}'. Check the symbol and date range.")
    st.stop()

info         = load_info(ticker)
company_name = info.get("longName", NAME_BY_TICKER.get(ticker, ticker))

latest_close = float(data["Close"].iloc[-1])
prev_close   = float(data["Close"].iloc[-2]) if len(data) > 1 else latest_close
change       = latest_close - prev_close
pct_change   = (change / prev_close * 100) if prev_close else 0
period_high  = float(data["High"].max())
period_low   = float(data["Low"].min())
avg_volume   = int(data["Volume"].mean())
market_cap   = info.get("marketCap")
pe_ratio     = info.get("trailingPE")
target_price = info.get("targetMeanPrice")

# Signal for this ticker
ticker_row = snapshot[snapshot["Ticker"] == ticker]
if not ticker_row.empty:
    sig, sig_cls = ticker_row.iloc[0]["Signal"], ticker_row.iloc[0]["SignalClass"]
    st.markdown(
        f'<h3 style="margin-bottom:4px">{company_name} <span style="color:#8892a4;font-size:1rem">({ticker})</span> &nbsp; '
        f'<span class="badge badge-{sig_cls}">{sig}</span></h3>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(f"### {company_name} ({ticker})")

# KPI row
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Price",       f"${latest_close:,.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
c2.metric("Period High", f"${period_high:,.2f}")
c3.metric("Period Low",  f"${period_low:,.2f}")
c4.metric("Avg Volume",  f"{avg_volume:,}")
c5.metric("Market Cap",  f"${market_cap/1e9:,.1f}B" if market_cap else "—")
c6.metric("P/E Ratio",   f"{pe_ratio:.1f}" if pe_ratio else "—")

# Analyst target
if target_price:
    upside = ((target_price - latest_close) / latest_close) * 100
    up_cls = "up" if upside >= 0 else "down"
    st.markdown(
        f'<p style="font-size:1.05rem;margin-top:4px">📌 Analyst consensus target: '
        f'<strong>${target_price:,.2f}</strong> &nbsp; '
        f'<span class="{up_cls}">({upside:+.1f}% from current price)</span></p>',
        unsafe_allow_html=True,
    )

# SMAs
for window, show in ((20, show_sma20), (50, show_sma50), (200, show_sma200)):
    if show:
        data[f"SMA{window}"] = data["Close"].rolling(window=window).mean()

# Candlestick chart
SMA_COLORS = {20: "#60a5fa", 50: "#f59e0b", 200: "#a78bfa"}
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"],
    name=ticker,
    increasing_line_color="#22c55e", increasing_fillcolor="#22c55e",
    decreasing_line_color="#f87171", decreasing_fillcolor="#f87171",
))
for window, show in ((20, show_sma20), (50, show_sma50), (200, show_sma200)):
    if show and f"SMA{window}" in data:
        fig.add_trace(go.Scatter(
            x=data.index, y=data[f"SMA{window}"],
            mode="lines", name=f"SMA {window}",
            line=dict(width=2, color=SMA_COLORS[window]),
        ))
fig.update_layout(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#131720",
    font=dict(color="#c0c8d8", size=13),
    xaxis_rangeslider_visible=False,
    height=480,
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis=dict(gridcolor="#1c2130", showgrid=True),
    yaxis=dict(gridcolor="#1c2130", showgrid=True, tickprefix="$"),
    legend=dict(bgcolor="#1c2130", bordercolor="#2a3040", borderwidth=1, font=dict(size=13)),
)
st.plotly_chart(fig, use_container_width=True)

# Volume chart
vol_colors = ["#22c55e" if c >= o else "#f87171" for c, o in zip(data["Close"], data["Open"])]
vol_fig = go.Figure(go.Bar(
    x=data.index, y=data["Volume"], name="Volume",
    marker_color=vol_colors, opacity=0.8,
))
vol_fig.add_trace(go.Scatter(
    x=data.index,
    y=data["Volume"].rolling(20).mean(),
    mode="lines", name="20D Avg",
    line=dict(color="#f59e0b", width=1.5, dash="dot"),
))
vol_fig.update_layout(
    paper_bgcolor="#0e1117", plot_bgcolor="#131720",
    font=dict(color="#c0c8d8", size=12),
    height=200, margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1c2130"), yaxis=dict(gridcolor="#1c2130"),
    legend=dict(bgcolor="#1c2130", font=dict(size=12)),
    showlegend=True,
)
st.plotly_chart(vol_fig, use_container_width=True)
st.caption("Green bars = closed up, red = closed down. Dotted line = 20-day average volume. Spikes often align with earnings or major news.")

with st.expander("Download raw data"):
    st.dataframe(data.sort_index(ascending=False))
    csv = data.to_csv().encode("utf-8")
    st.download_button("Download CSV", csv, file_name=f"{ticker}_{start_date}_{end_date}.csv")

with st.expander("📚 Key terms"):
    st.markdown("""
- **Signal** — our composite score: momentum over 5 days + price vs SMA20 + volume activity
- **5D Momentum** — % price change over the last 5 trading days; positive = uptrend
- **P/E Ratio** — price ÷ earnings per share; lower can mean cheaper relative to peers
- **Analyst Target** — Wall Street consensus price target; shows expected upside/downside
- **SMA (Simple Moving Average)** — average price over N days; price above SMA = bullish trend
- **Volume spike** — unusually high trading activity, often tied to news or earnings
    """)

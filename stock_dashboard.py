import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="SEMIS // MARKET SCANNER", layout="wide", page_icon="⚡")

# ── Dark cyberpunk CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap');

html, body, [class*="css"] {
    background-color: #080b12 !important;
    color: #c9d1d9 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid #00f5c420 !important;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* Main background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #080b12 0%, #0d1117 100%) !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #0d1117;
    border: 1px solid #00f5c430;
    border-radius: 4px;
    padding: 16px 20px !important;
    box-shadow: 0 0 12px #00f5c410;
}
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.75rem !important; letter-spacing: 2px; text-transform: uppercase; }
[data-testid="stMetricValue"] { color: #00f5c4 !important; font-family: 'Share Tech Mono', monospace !important; font-size: 1.6rem !important; }

/* Divider */
hr { border-color: #00f5c420 !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #00f5c420 !important;
    border-radius: 4px;
}

/* Headings */
h1 {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 4px !important;
    color: #ffffff !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid #00f5c4 !important;
    padding-bottom: 8px !important;
}
h2, h3 {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 3px !important;
    color: #00f5c4 !important;
    text-transform: uppercase !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: #00f5c4 !important; }

/* Select / radio */
[data-testid="stSelectbox"] select,
[data-testid="stRadio"] label { color: #c9d1d9 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #00f5c440; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

SEMIS = {
    "NVDA":  "NVIDIA",
    "AMD":   "AMD",
    "INTC":  "Intel",
    "QCOM":  "Qualcomm",
    "AVGO":  "Broadcom",
    "TXN":   "Texas Instruments",
    "AMAT":  "Applied Materials",
    "LRCX":  "Lam Research",
    "KLAC":  "KLA Corp",
    "MU":    "Micron",
    "MRVL":  "Marvell",
    "ADI":   "Analog Devices",
    "MCHP":  "Microchip Tech",
    "ON":    "ON Semiconductor",
    "MPWR":  "Monolithic Power",
    "SWKS":  "Skyworks",
    "QRVO":  "Qorvo",
    "LSCC":  "Lattice Semi",
    "ENTG":  "Entegris",
    "TER":   "Teradyne",
    "ASML":  "ASML",
    "TSM":   "TSMC",
    "SLAB":  "Silicon Labs",
    "CAMT":  "Camtek",
    "ACLS":  "Axcelis Tech",
    "WOLF":  "Wolfspeed",
    "COHU":  "Cohu",
}

COLORS = {
    "bg":       "#080b12",
    "surface":  "#0d1117",
    "accent":   "#00f5c4",
    "red":      "#ff4d6d",
    "green":    "#00f5c4",
    "grid":     "#1c2333",
    "text":     "#c9d1d9",
    "muted":    "#8b949e",
}

@st.cache_data(ttl=900)
def fetch_changes(tickers: list[str]) -> pd.DataFrame:
    today = datetime.today().date()
    start = today - timedelta(days=370)
    raw = yf.download(tickers, start=str(start), end=str(today), auto_adjust=True, progress=False)
    close = raw["Close"] if len(tickers) > 1 else raw[["Close"]].rename(columns={"Close": tickers[0]})

    rows = []
    for ticker in tickers:
        if ticker not in close.columns:
            continue
        series = close[ticker].dropna()
        if len(series) < 2:
            continue
        price_now = series.iloc[-1]
        price_1m  = series.iloc[max(0, len(series) - 22)]
        price_1y  = series.iloc[0]
        rows.append({
            "Ticker":      ticker,
            "Company":     SEMIS.get(ticker, ticker),
            "Price":       round(price_now, 2),
            "1M Change %": round((price_now - price_1m) / price_1m * 100, 2),
            "1Y Change %": round((price_now - price_1y) / price_1y * 100, 2),
        })
    return pd.DataFrame(rows).set_index("Ticker")


def plotly_dark_layout(**kwargs):
    return dict(
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["surface"],
        font=dict(family="Share Tech Mono, monospace", color=COLORS["text"], size=12),
        xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["muted"], tickfont=dict(color=COLORS["muted"])),
        yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["muted"], tickfont=dict(color=COLORS["muted"])),
        **kwargs,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## ⚡ SCANNER")
sort_by   = st.sidebar.selectbox("SORT BY", ["1Y Change %", "1M Change %", "Price", "Company"])
ascending = st.sidebar.checkbox("Ascending", value=False)
show_chart = st.sidebar.radio("CHART VIEW", ["Monthly", "Yearly", "Both"])

# ── Data ──────────────────────────────────────────────────────────────────────
with st.spinner("Scanning markets…"):
    df = fetch_changes(list(SEMIS.keys()))
df = df.sort_values(sort_by, ascending=ascending)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# ⚡ Semis // Market Scanner")
st.markdown(
    f"<span style='font-family:Share Tech Mono;color:#8b949e;font-size:0.8rem;letter-spacing:2px'>"
    f"LAST UPDATE: {datetime.today().strftime('%Y-%m-%d %H:%M')} · REFRESH 15MIN · 27 TICKERS</span>",
    unsafe_allow_html=True,
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
gainers_1m = (df["1M Change %"] > 0).sum()
gainers_1y = (df["1Y Change %"] > 0).sum()
avg_1m = df["1M Change %"].mean()
avg_1y = df["1Y Change %"].mean()
top_1m = df["1M Change %"].idxmax()
top_1y = df["1Y Change %"].idxmax()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("TRACKED", len(df))
k2.metric("1M GAINERS", f"{gainers_1m} / {len(df) - gainers_1m}")
k3.metric("1Y GAINERS", f"{gainers_1y} / {len(df) - gainers_1y}")
k4.metric("AVG 1M", f"{avg_1m:+.1f}%")
k5.metric("AVG 1Y", f"{avg_1y:+.1f}%")
k6.metric("TOP 1Y", top_1y)

st.divider()

# ── Table ─────────────────────────────────────────────────────────────────────
def color_pct(val):
    if val > 30:   bg, fg = "#003d2e", "#00f5c4"
    elif val > 10: bg, fg = "#00261c", "#00e6b5"
    elif val > 0:  bg, fg = "#001a14", "#00c99c"
    elif val > -10: bg, fg = "#2a0a10", "#ff4d6d"
    elif val > -30: bg, fg = "#3d0c16", "#ff2d52"
    else:           bg, fg = "#500d1a", "#ff1744"
    return f"background-color: {bg}; color: {fg}; font-weight: 700; font-family: 'Share Tech Mono', monospace; letter-spacing: 1px"

display_df = df[["Company", "Price", "1M Change %", "1Y Change %"]].copy()
styled = (
    display_df.style
    .map(color_pct, subset=["1M Change %", "1Y Change %"])
    .format({"Price": "${:.2f}", "1M Change %": "{:+.2f}%", "1Y Change %": "{:+.2f}%"})
    .set_properties(**{"background-color": "#0d1117", "color": "#c9d1d9", "border-color": "#1c2333"})
)

st.markdown("### Performance Table")
st.dataframe(styled, use_container_width=True, height=620)

st.divider()

# ── Bar charts ────────────────────────────────────────────────────────────────
def make_bar(col: str, title: str):
    s = df.sort_values(col, ascending=True)
    colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in s[col]]
    fig = go.Figure(go.Bar(
        x=s[col],
        y=s.index,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+.1f}%" for v in s[col]],
        textposition="outside",
        textfont=dict(family="Share Tech Mono", size=10, color=COLORS["text"]),
        hovertemplate="<b>%{y}</b><br>" + col + ": %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(family="Rajdhani", size=16, color=COLORS["accent"]), x=0),
        height=720,
        margin=dict(l=80, r=80, t=50, b=30),
        xaxis=dict(
            zeroline=True, zerolinecolor=COLORS["muted"], zerolinewidth=1,
            gridcolor=COLORS["grid"], tickfont=dict(family="Share Tech Mono", color=COLORS["muted"]),
        ),
        yaxis=dict(tickfont=dict(family="Share Tech Mono", size=11, color=COLORS["text"])),
        **{k: v for k, v in plotly_dark_layout().items() if k not in ("xaxis", "yaxis")},
    )
    return fig

if show_chart in ("Both", "Monthly"):
    st.markdown("### 1-Month Change")
    st.plotly_chart(make_bar("1M Change %", "1-MONTH PRICE CHANGE"), use_container_width=True)

if show_chart in ("Both", "Yearly"):
    st.markdown("### 1-Year Change")
    st.plotly_chart(make_bar("1Y Change %", "1-YEAR PRICE CHANGE"), use_container_width=True)

# ── Scatter ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 1M vs 1Y Momentum Map")

fig_scatter = go.Figure()
for _, row in df.reset_index().iterrows():
    clr = COLORS["green"] if row["1Y Change %"] >= 0 else COLORS["red"]
    fig_scatter.add_trace(go.Scatter(
        x=[row["1M Change %"]],
        y=[row["1Y Change %"]],
        mode="markers+text",
        marker=dict(size=max(8, min(row["Price"] ** 0.4, 36)), color=clr, opacity=0.85,
                    line=dict(color=clr, width=1)),
        text=[row["Ticker"]],
        textposition="top center",
        textfont=dict(family="Share Tech Mono", size=10, color=COLORS["text"]),
        hovertemplate=f"<b>{row['Ticker']}</b> — {row['Company']}<br>"
                      f"Price: ${row['Price']:.2f}<br>"
                      f"1M: {row['1M Change %']:+.2f}%<br>"
                      f"1Y: {row['1Y Change %']:+.2f}%<extra></extra>",
        name=row["Ticker"],
        showlegend=False,
    ))

fig_scatter.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], line_width=1)
fig_scatter.add_vline(x=0, line_dash="dot", line_color=COLORS["muted"], line_width=1)
fig_scatter.update_layout(
    height=580,
    xaxis_title="1M Change %",
    yaxis_title="1Y Change %",
    **plotly_dark_layout(),
)
st.plotly_chart(fig_scatter, use_container_width=True)

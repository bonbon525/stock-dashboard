import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Semis Stock Dashboard", layout="wide")

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

@st.cache_data(ttl=900)
def fetch_changes(tickers: list[str]) -> pd.DataFrame:
    today = datetime.today().date()
    start = today - timedelta(days=370)
    raw = yf.download(
        tickers,
        start=str(start),
        end=str(today),
        auto_adjust=True,
        progress=False,
    )
    close = raw["Close"] if len(tickers) > 1 else raw[["Close"]].rename(columns={"Close": tickers[0]})

    rows = []
    for ticker in tickers:
        if ticker not in close.columns:
            continue
        series = close[ticker].dropna()
        if len(series) < 2:
            continue

        price_now = series.iloc[-1]

        # Monthly: ~21 trading days back
        idx_1m = max(0, len(series) - 22)
        price_1m = series.iloc[idx_1m]

        # Yearly: earliest available (≈1 year)
        price_1y = series.iloc[0]

        rows.append({
            "Ticker": ticker,
            "Company": SEMIS.get(ticker, ticker),
            "Price": round(price_now, 2),
            "1M Change %": round((price_now - price_1m) / price_1m * 100, 2),
            "1Y Change %": round((price_now - price_1y) / price_1y * 100, 2),
        })

    return pd.DataFrame(rows).set_index("Ticker")


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("Semis Dashboard")
sort_by = st.sidebar.selectbox("Sort by", ["1Y Change %", "1M Change %", "Price", "Company"])
ascending = st.sidebar.checkbox("Ascending", value=False)
show_chart = st.sidebar.radio("Chart view", ["Monthly", "Yearly", "Both"])

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Fetching prices…"):
    df = fetch_changes(list(SEMIS.keys()))

df = df.sort_values(sort_by, ascending=ascending)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Semiconductor Stocks — Monthly & Yearly Performance")
st.caption(f"Prices as of {datetime.today().strftime('%b %d, %Y')}  ·  refreshes every 15 min")

# ── KPI row ──────────────────────────────────────────────────────────────────
gainers_1m = (df["1M Change %"] > 0).sum()
gainers_1y = (df["1Y Change %"] > 0).sum()
avg_1m = df["1M Change %"].mean()
avg_1y = df["1Y Change %"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Stocks tracked", len(df))
k2.metric("1M gainers / losers", f"{gainers_1m} / {len(df) - gainers_1m}")
k3.metric("Avg 1M change", f"{avg_1m:+.1f}%")
k4.metric("Avg 1Y change", f"{avg_1y:+.1f}%")

st.divider()

# ── Color-coded table ────────────────────────────────────────────────────────
def color_pct(val):
    if val > 20:
        bg = "#1a7a3a"
    elif val > 5:
        bg = "#2d9e50"
    elif val > 0:
        bg = "#5cb87a"
    elif val > -5:
        bg = "#c0392b"
    elif val > -20:
        bg = "#962d22"
    else:
        bg = "#6b1a13"
    return f"background-color: {bg}; color: white; font-weight: 600"

display_df = df[["Company", "Price", "1M Change %", "1Y Change %"]].copy()
styled = (
    display_df.style
    .applymap(color_pct, subset=["1M Change %", "1Y Change %"])
    .format({"Price": "${:.2f}", "1M Change %": "{:+.2f}%", "1Y Change %": "{:+.2f}%"})
)

st.subheader("Performance Table")
st.dataframe(styled, use_container_width=True, height=600)

st.divider()

# ── Bar charts ────────────────────────────────────────────────────────────────
def make_bar(col: str, title: str):
    sorted_df = df.sort_values(col, ascending=True)
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in sorted_df[col]]
    fig = go.Figure(go.Bar(
        x=sorted_df[col],
        y=sorted_df.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in sorted_df[col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + col + ": %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=title,
        xaxis_title="% Change",
        yaxis_title="",
        height=700,
        margin=dict(l=80, r=60, t=50, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(zeroline=True, zerolinecolor="#555", gridcolor="#333"),
    )
    return fig


if show_chart in ("Both", "Monthly"):
    st.subheader("1-Month Change (%)")
    st.plotly_chart(make_bar("1M Change %", "1-Month Price Change"), use_container_width=True)

if show_chart in ("Both", "Yearly"):
    st.subheader("1-Year Change (%)")
    st.plotly_chart(make_bar("1Y Change %", "1-Year Price Change"), use_container_width=True)

# ── Scatter: 1M vs 1Y ────────────────────────────────────────────────────────
st.divider()
st.subheader("1-Month vs 1-Year Change")
fig_scatter = px.scatter(
    df.reset_index(),
    x="1M Change %",
    y="1Y Change %",
    text="Ticker",
    color="1Y Change %",
    color_continuous_scale="RdYlGn",
    size="Price",
    size_max=40,
    hover_data={"Company": True, "Price": True},
)
fig_scatter.update_traces(textposition="top center")
fig_scatter.add_hline(y=0, line_dash="dash", line_color="#555")
fig_scatter.add_vline(x=0, line_dash="dash", line_color="#555")
fig_scatter.update_layout(
    height=550,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_scatter, use_container_width=True)

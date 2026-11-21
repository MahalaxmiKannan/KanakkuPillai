"""Simulator: a range of outcomes for a monthly SIP, built from real Nifty 50 history."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.simulator import load_monthly_returns, simulate
from core.spending import format_inr
from core.ui import page_header, setup_page

setup_page("Simulator", "📈")
page_header("Simulator", "📈", "A range of possible outcomes for a monthly SIP, never a prediction.", step=6)


@st.cache_data
def history():
    return load_monthly_returns()


@st.cache_data(show_spinner="Running 10,000 simulations...")
def run(monthly: float, years: int, inflation: float | None, fd_rate: float) -> dict:
    return simulate(monthly, years, history()["return"].to_numpy(), inflation, fd_rate)


data = history()
surplus = st.session_state.get("surplus")
default = int(surplus["safe_to_set_aside"]) if surplus and surplus["safe_to_set_aside"] > 0 else 2000

with st.sidebar:
    st.header("Your plan")
    monthly = st.number_input("Monthly amount (₹)", min_value=100, max_value=1_000_000, value=max(default, 100), step=500)
    if surplus and surplus["safe_to_set_aside"] > 0:
        st.caption(f"Filled in from My Surplus ({format_inr(surplus['safe_to_set_aside'])} a month).")
    years = st.slider("Years", 1, 15, 10)
    st.caption("Up to 15 years: the history is only about 19 years long, so longer paths would mostly repeat the same stretches.")
    adjust = st.toggle("Show in today's money (adjust for inflation)", value=True)
    inflation = st.number_input("Inflation per year (%)", 0.0, 15.0, 6.0, 0.5, disabled=not adjust) / 100
    fd_rate = st.number_input("FD / RD rate per year (%)", 0.0, 12.0, 7.0, 0.25) / 100

r = run(float(monthly), years, inflation if adjust else None, fd_rate)
money = "in today's money" if adjust else "in future rupees"

c1, c2, c3, c4 = st.columns(4)
c1.metric("You put in", format_inr(r["total_invested"]))
c2.metric("Bad case (1 in 10 worse)", format_inr(r["final"][10]))
c3.metric("Middle case", format_inr(r["final"][50]))
c4.metric("Good case (1 in 10 better)", format_inr(r["final"][90]))
st.caption(f"Values after {years} year(s), {money}.")

below = r["chance_below_invested"]
st.info(
    f"In **{below:.0%}** of the simulated paths you end with fewer rupees than you put in. "
    f"In **{r['chance_below_fd']:.0%}** you end below the {fd_rate:.1%} FD line."
)

x = np.arange(1, r["months"] + 1) / 12
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=r["bands"][90], line=dict(width=0), hoverinfo="skip", showlegend=False))
fig.add_trace(go.Scatter(x=x, y=r["bands"][10], fill="tonexty", fillcolor="rgba(46,134,222,0.22)",
                         line=dict(width=0), name="10th to 90th percentile"))
fig.add_trace(go.Scatter(x=x, y=r["bands"][50], line=dict(color="#2e86de", width=3), name="Middle (median)"))
fig.add_trace(go.Scatter(x=x, y=r["fd"], line=dict(color="#e67e22", dash="dash"), name=f"FD at {fd_rate:.1%}"))
fig.add_trace(go.Scatter(x=x, y=r["invested"], line=dict(color="#7f8c8d", dash="dot"), name="Money put in"))
fig.update_layout(
    xaxis_title="Years", yaxis_title=f"Value (₹, {money})", hovermode="x unified",
    legend=dict(orientation="h", y=-0.2), margin=dict(t=20, l=10, r=10), height=460,
)
fig.update_yaxes(tickprefix="₹", separatethousands=True)
st.plotly_chart(fig, width="stretch")

with st.expander("Assumptions and limits", expanded=True):
    st.markdown(
        f"""
- **Data:** Nifty 50 month-end closes, {data['month'].iloc[0]} to {data['month'].iloc[-1]} ({len(data)} months, from Yahoo Finance `^NSEI`).
- **Method:** 10,000 paths, each made of random real 12-month stretches of Nifty returns glued together (block bootstrap). Money goes in at the start of each month.
- **Price index only:** dividends are not included, so this slightly understates an index fund. **No fees, taxes or expense ratio** are taken off.
- The FD line assumes the rate stays fixed for the whole period.
- {"Values are divided by inflation of " + f"{inflation:.1%}" + " a year, so they show buying power today." if adjust else "Values are not adjusted for inflation."}
- **These ranges come from 2007 to 2026 only, and that may be kinder than the future.** Over that stretch the index rose about 8.3% a year, not counting dividends.
- **Past returns don't predict future returns.** The real range could be wider than this.
- Years are capped at 15 because a 20-year path built from about 19 years of history would mostly reuse the same stretches.
"""
    )
st.page_link("pages/7_Scam_Checker.py", label="Next: Scam checker →")

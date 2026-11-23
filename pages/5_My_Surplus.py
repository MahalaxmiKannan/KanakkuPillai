"""My Surplus on one screen: the month as a single bar, a what-if lever, and the runway to an emergency fund."""
import math

import plotly.graph_objects as go
import streamlit as st

from core.spending import format_inr
from core.surplus import avoidable_per_month, compute_surplus, describe_duration, months_to_full, runway
from core.ui import empty_state, load_categorized, setup_page, step_tracker

setup_page("My Surplus", "🏦")

mode = "dark" if st.context.theme.type == "dark" else "light"
INK = {
    "light": {"text": "#0b0b0b", "muted": "#52514e", "grid": "#e6e5e0", "surface": "#ffffff", "track": "#e8ece9"},
    "dark": {"text": "#f0efec", "muted": "#c3c2b7", "grid": "#33332f", "surface": "#0e1117", "track": "#27302d"},
}[mode]
SEG = {"Essentials": "#3f8f77", "Avoidable": "#e07a5f", "Other spending": "#c9b88f", "Sent to people": "#8a97a0",
       "Left over": "#e9c46a", "Over budget": "#c2412d"}
GOLD, TEAL = "#e9c46a", "#14b8a6"
PLOT = {"displayModeBar": False}

# One screen on a laptop: tighter spacing on this page only.
st.markdown(
    """
<style>
  .block-container { padding-top: .9rem !important; padding-bottom: .4rem !important; }
  [data-testid="stVerticalBlock"] { gap: .7rem !important; }
  .sp-title { font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.1; margin: 0; }
  .sp-sub { opacity: .72; font-size: .95rem; margin-top: .15rem; }
  .sp-leg { display: flex; flex-wrap: wrap; gap: .25rem 1.1rem; font-size: .86rem; margin-top: -.2rem; }
  .sp-leg i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; }
  .sp-leg b { font-weight: 700; }
  .sp-tile { border-radius: 16px; padding: .7rem .9rem; border: 1px solid var(--kp-line); background: var(--kp-soft); }
  .sp-tile.hot { border-color: rgba(27,127,92,.55); background: rgba(27,127,92,.09); }
  .sp-k { font-size: .72rem; letter-spacing: .09em; text-transform: uppercase; opacity: .7; font-weight: 700; }
  .sp-v { font-size: 1.55rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; }
  .sp-d { font-size: .86rem; opacity: .82; }
  @media (max-width: 760px) { .sp-title { font-size: 1.35rem; } }
</style>
""",
    unsafe_allow_html=True,
)

df = load_categorized()
if df is None:
    empty_state("Your surplus is worked out from a statement, so load one first.", ("Go to Upload", "pages/1_Upload.py"))
    st.stop()

# ---------- header + adjustments ----------
step_tracker(5)
quiz = st.session_state.get("risk_result")
quiz_note = f" · quiz profile: {quiz['profile']}" if quiz else ""
head, adjust = st.columns([5, 1.1], vertical_alignment="center")
head.markdown('<div class="sp-title">🏦 My Surplus</div>'
              f'<div class="sp-sub">What is left each month, and how fast it could become an emergency fund{quiz_note}</div>',
              unsafe_allow_html=True)
with adjust.popover("⚙ Adjust", width="stretch"):
    detected = compute_surplus(df)["income_detected"]
    use_override = st.toggle("Enter my own monthly income", value=detected <= 0,
                             help="Use this if your income isn't in the statement, or the detected figure is wrong.")
    override = st.number_input("Monthly income (₹)", min_value=0, value=int(detected), step=500) if use_override else None
    irregular = st.toggle("My income is irregular", help="Aims for 6 months of essentials instead of 3.")
    saved = st.number_input("Emergency savings I already have (₹)", min_value=0, value=0, step=1000)
    count_transfers = st.toggle("Count money I sent to people as spending",
                                help="Payments to people aren't counted by default, because the app can't see what they were for. "
                                     "Turn this on if they were really rent, shared bills or food.")
months_target = 6 if irregular else 3

r = compute_surplus(df, override, months_target, float(saved), count_transfers)
st.session_state["surplus"] = r            # the Simulator pre-fills from this

if override is None and r["income_detected"] <= 0:
    st.warning("No income was found in this statement. Open **Adjust** and enter your monthly income.")
elif r["months"] < 3:
    st.caption(f"This statement covers only {r['months']} month(s), so these averages are rough.")

# ---------- the month as one bar ----------
income = r["income"]
avoid = min(avoidable_per_month(df), r["discretionary"])
other = max(r["discretionary"] - avoid, 0.0)
parts = [("Essentials", r["essentials"]), ("Avoidable", avoid), ("Other spending", other)]
if r["transfers_counted"] > 0:
    parts.append(("Sent to people", r["transfers_counted"]))
parts.append(("Over budget" if r["surplus"] < 0 else "Left over", abs(r["surplus"])))
scale = max(income, r["spend"], 1.0)


def month_bar() -> go.Figure:
    fig = go.Figure()
    for name, value in parts:
        share = value / scale
        fig.add_bar(
            x=[value], y=[""], orientation="h", name=name, marker={"color": SEG[name], "line": {"color": INK["surface"], "width": 2}},
            text=[f"{share:.0%}"] if share >= 0.07 else [""], textposition="inside", insidetextanchor="middle",
            textfont={"color": "#ffffff" if name in ("Essentials", "Avoidable", "Over budget", "Sent to people") else "#2b2518", "size": 15},
            customdata=[[format_inr(value), f"₹{100 * share:.0f}"]],
            hovertemplate="<b>" + name + "</b><br>%{customdata[0]} a month<br>%{customdata[1]} of every ₹100<extra></extra>",
        )
    fig.update_layout(
        barmode="stack", height=74, showlegend=False, margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=0, barcornerradius=10,
        font={"color": INK["muted"]}, hoverlabel={"bgcolor": INK["surface"], "font": {"color": INK["text"]}},
    )
    fig.update_xaxes(visible=False, range=[0, scale])
    fig.update_yaxes(visible=False)
    return fig


with st.container(border=True, key="card_monthbar"):
    st.markdown(f"**Where each month's {format_inr(income)} goes**")
    st.plotly_chart(month_bar(), width="stretch", theme=None, config=PLOT)
    st.markdown('<div class="sp-leg">' + "".join(
        f'<span><i style="background:{SEG[n]}"></i>{n} <b>{format_inr(v)}</b> · {v / scale:.0%}</span>' for n, v in parts) + "</div>",
        unsafe_allow_html=True)

# ---------- the lever ----------
lever_l, lever_r = st.columns([2.2, 3], vertical_alignment="center")
trim = lever_l.slider("What if you trimmed avoidable spending by…", 0, 100, 25, 5, format="%d%%",
                      help="Food & dining, shopping and subscriptions. A what-if, not advice: it shows the arithmetic.")
gain = avoid * trim / 100
w = compute_surplus(df, income + gain, months_target, float(saved), count_transfers)
lever_r.markdown(
    f"<div class='sp-sub' style='margin:0'>Food delivery, shopping and subscriptions cost <b>{format_inr(avoid)}</b> a month. "
    f"Trimming <b>{trim}%</b> frees <b>{format_inr(gain)}</b> a month.</div>", unsafe_allow_html=True)

target, have = r["emergency_target"], float(saved)
m_now = months_to_full(r["safe_to_set_aside"], have, target)
m_new = months_to_full(w["safe_to_set_aside"], have, target)

# ---------- runway chart + the numbers ----------
chart_col, side_col = st.columns([3, 2])


def runway_chart() -> go.Figure:
    horizon = 12 if m_new is None else int(min(60, max(12, math.ceil(m_new) + 6)))
    xs = list(range(horizon + 1))
    fig = go.Figure()
    fig.add_scatter(x=xs, y=runway(r["safe_to_set_aside"], have, target, horizon), mode="lines", name="Right now",
                    line={"color": INK["muted"], "width": 2.5, "dash": "dot"},
                    hovertemplate="Right now: ₹%{y:,.0f}<extra></extra>")
    fig.add_scatter(x=xs, y=runway(w["safe_to_set_aside"], have, target, horizon), mode="lines", name=f"With a {trim}% trim",
                    line={"color": TEAL, "width": 4}, fill="tozeroy", fillcolor="rgba(20,184,166,.12)",
                    hovertemplate="With the trim: ₹%{y:,.0f}<extra></extra>")
    if m_new is not None and 0 < m_new <= horizon:
        fig.add_scatter(x=[m_new], y=[target], mode="markers+text", showlegend=False, hoverinfo="skip",
                        marker={"size": 12, "color": TEAL, "line": {"color": INK["surface"], "width": 3}},
                        text=[f"full in {describe_duration(m_new)}"], textposition="top left", textfont={"color": INK["text"], "size": 13})
    fig.add_hline(y=target, line={"color": GOLD, "dash": "dash", "width": 2}, annotation_text=f"target {format_inr(target)}",
                  annotation_position="bottom right", annotation_font={"color": INK["muted"], "size": 12})
    fig.update_layout(
        height=246, margin={"l": 8, "r": 12, "t": 8, "b": 8}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": INK["muted"], "size": 12}, hovermode="x unified",
        hoverlabel={"bgcolor": INK["surface"], "font": {"color": INK["text"]}},
        legend={"orientation": "h", "y": 1.12, "x": 0}, xaxis_title="Months from now",
    )
    fig.update_xaxes(showgrid=False, linecolor=INK["grid"], dtick=6 if horizon <= 36 else 12, rangemode="tozero", automargin=True)
    fig.update_yaxes(gridcolor=INK["grid"], zeroline=False, tickprefix="₹", tickformat="~s", range=[0, max(target, 1) * 1.15], automargin=True)
    return fig


with chart_col:
    st.markdown("**Runway to your emergency fund**")
    if target <= 0:
        st.info("No essential spending was found, so there is no emergency-fund target yet.")
    else:
        st.plotly_chart(runway_chart(), width="stretch", theme=None, config=PLOT)

with side_col:
    free_after = f" Then {format_inr(w['safe_to_set_aside'])} a month is free." if w["safe_to_set_aside"] > 0 and target > have else ""
    n1, n2 = st.columns(2)
    n1.markdown(f"<div class='sp-tile'><div class='sp-k'>Right now</div><div class='sp-v'>{format_inr(r['safe_to_set_aside'])}</div>"
                f"<div class='sp-d'>a month · fund full in <b>{describe_duration(m_now)}</b></div></div>", unsafe_allow_html=True)
    n2.markdown(f"<div class='sp-tile hot'><div class='sp-k'>With the trim</div><div class='sp-v'>{format_inr(w['safe_to_set_aside'])}</div>"
                f"<div class='sp-d'>a month · full in <b>{describe_duration(m_new)}</b></div></div>", unsafe_allow_html=True)

    pct = min(have / target, 1.0) if target > 0 else 1.0
    fund = go.Figure(go.Pie(values=[max(pct, 0.0001), max(1 - pct, 0.0001)], hole=0.78, sort=False, direction="clockwise",
                            marker={"colors": [GOLD, INK["track"]], "line": {"color": INK["surface"], "width": 2}},
                            textinfo="none", hoverinfo="skip", showlegend=False))
    fund.update_layout(height=128, margin={"l": 0, "r": 0, "t": 0, "b": 0}, paper_bgcolor="rgba(0,0,0,0)",
                       annotations=[{"text": f"<b>{pct:.0%}</b><br><span style='font-size:11px'>of {format_inr(target)}</span>",
                                     "showarrow": False, "font": {"size": 22, "color": INK["text"]}}])
    ring, words = st.columns([1, 1.7], vertical_alignment="center")
    ring.plotly_chart(fund, width="stretch", theme=None, config=PLOT)
    words.markdown(f"<div class='sp-d'><b>Emergency fund first.</b> {months_target} months of essentials "
                   f"({format_inr(target)}) before any investment risk.{free_after} Arithmetic on past spending, not advice.</div>", unsafe_allow_html=True)

    if w["safe_to_set_aside"] > 0:
        if st.button(f"Simulate {format_inr(w['safe_to_set_aside'])} a month →", type="primary", width="stretch"):
            st.session_state["surplus"] = w
            st.switch_page("pages/6_Simulator.py")
    else:
        st.caption("Your spending is at or above your income, so there is nothing safe to set aside yet. "
                   "Try a bigger trim, or see My Spending for the biggest categories.")
        st.page_link("pages/6_Simulator.py", label="Skip to the Simulator →")

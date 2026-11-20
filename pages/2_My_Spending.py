"""Spending dashboard: where the money went, with categories the user can correct."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.categorizer import CATEGORIES, SPENDING_CATEGORIES, categorize, load_model
from core.parsers import find_balance_gaps, parse_statement
from core.spending import (
    AVOIDABLE_CATEGORIES,
    apply_overrides,
    by_category,
    format_inr,
    monthly_trend,
    recurring_payments,
    same_payee_ids,
    summary,
    top_merchants,
)
from core.ui import clear_user_data, load_categorized, setup_page

setup_page("My Spending", "📊")

DEMO_FILE = Path(__file__).resolve().parents[1] / "data" / "demo_statement.csv"

# Fixed slot per category, so a color always means the same thing.
SERIES = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"],
}
INK = {
    "light": {"text": "#0b0b0b", "muted": "#52514e", "grid": "#e6e5e0", "surface": "#ffffff"},
    "dark": {"text": "#f0efec", "muted": "#c3c2b7", "grid": "#33332f", "surface": "#0e1117"},
}
SOURCE_LABELS = {
    "rule": "App rules",
    "model": "ML model",
    "person": "Looks like a person",
    "fallback": "Best guess",
    "you": "Your correction",
}

mode = "dark" if st.context.theme.type == "dark" else "light"
# The palette is validated for 8 categories; any further ones get neutral greys.
EXTRA = {"light": ["#8a8984", "#b9b8b2"], "dark": ["#9d9c95", "#6c6b66"]}
colors = dict(zip(SPENDING_CATEGORIES, SERIES[mode] + EXTRA[mode]))
ink = INK[mode]
PLOT_CONFIG = {"displayModeBar": False}


def base_layout(height: int) -> dict:
    return {
        "height": height,
        "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": ink["muted"], "size": 13},
        "hoverlabel": {"bgcolor": ink["surface"], "font": {"color": ink["text"]}, "bordercolor": ink["grid"]},
    }


def donut(totals: pd.Series) -> go.Figure:
    share = totals / totals.sum()
    fig = go.Figure(go.Pie(
        labels=totals.index,
        values=totals.values,
        hole=0.64,
        sort=False,
        direction="clockwise",
        marker={"colors": [colors[c] for c in totals.index], "line": {"color": ink["surface"], "width": 2}},
        text=[f"{s:.0%}" if s >= 0.06 else "" for s in share],
        textinfo="text",
        textposition="outside",
        textfont={"color": ink["text"]},
        customdata=[format_inr(v) for v in totals.values],
        hovertemplate="<b>%{label}</b><br>%{customdata} · %{percent}<extra></extra>",
    ))
    fig.update_layout(
        **base_layout(380),
        legend={"orientation": "h", "y": -0.08, "x": 0.5, "xanchor": "center"},
        annotations=[{
            "text": f"<b>{format_inr(totals.sum())}</b><br><span style='font-size:12px'>total spent</span>",
            "showarrow": False,
            "font": {"size": 20, "color": ink["text"]},
        }],
    )
    return fig


def trend_line(trend: pd.Series) -> go.Figure:
    labels = [p.strftime("%b %y") for p in trend.index]
    peak = trend.values.argmax()
    fig = go.Figure(go.Scatter(
        x=labels,
        y=trend.values,
        mode="lines+markers+text",
        line={"color": SERIES[mode][0], "width": 2},
        marker={"size": 9, "color": SERIES[mode][0], "line": {"color": ink["surface"], "width": 2}},
        text=[format_inr(v) if i == peak else "" for i, v in enumerate(trend.values)],
        textposition="top center",
        textfont={"color": ink["text"]},
        customdata=[format_inr(v) for v in trend.values],
        hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(**base_layout(380), showlegend=False)
    fig.update_xaxes(type="category", showgrid=False, linecolor=ink["grid"], automargin=True)
    fig.update_yaxes(
        rangemode="tozero",
        range=[0, float(trend.max()) * 1.18 or 1],
        gridcolor=ink["grid"],
        zeroline=False,
        tickprefix="₹",
        tickformat="~s",
        automargin=True,
    )
    return fig


def merchant_bars(top: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=top["amount"],
        y=top["payee"].str.title(),
        orientation="h",
        marker={"color": SERIES[mode][0], "cornerradius": 4},
        text=[format_inr(v) for v in top["amount"]],
        textposition="outside",
        textfont={"color": ink["text"]},
        cliponaxis=False,
        customdata=list(zip(top["category"], top["payments"])),
        hovertemplate="<b>%{y}</b><br>%{text} over %{customdata[1]} payments<br>%{customdata[0]}<extra></extra>",
    ))
    layout = base_layout(max(240, 38 * len(top)))
    layout["margin"] = {"l": 8, "r": 76, "t": 8, "b": 8}
    fig.update_layout(**layout, bargap=0.42, showlegend=False)
    fig.update_xaxes(visible=False, rangemode="tozero")
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", linecolor=ink["grid"], automargin=True)
    return fig


def save_edits(editor_key: str, row_ids: list[int]) -> None:
    """Store the user's category changes, then rebuild the table from them."""
    current = apply_overrides(st.session_state["categorized"], st.session_state["category_overrides"])
    every_row = st.session_state.get("apply_to_payee", True)
    for position, change in st.session_state[editor_key]["edited_rows"].items():
        category = change.get("category")
        if category:
            txn_id = row_ids[int(position)]
            targets = same_payee_ids(current, txn_id) if every_row else [txn_id]
            st.session_state["category_overrides"].update({t: category for t in targets})
    st.session_state["editor_version"] += 1


def reset_edits() -> None:
    st.session_state["category_overrides"] = {}
    st.session_state["editor_version"] += 1


st.title("📊 My Spending")

raw = st.session_state.get("transactions")
if raw is None:
    st.info("No statement loaded yet. Upload yours, or explore with a fictional student's account.")
    left, right, _ = st.columns([1, 1, 2])
    if left.button("Try the demo", type="primary", width="stretch"):
        st.session_state["transactions"] = parse_statement(DEMO_FILE, "standard")
        st.session_state["source_name"] = "Demo statement"
        st.session_state["use_demo"] = True
        st.rerun()
    if right.button("Upload my statement", width="stretch"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

# Categorize once per statement; corrections survive moving between pages.
df = load_categorized()

st.caption(f"Showing: {st.session_state.get('source_name', 'statement')}")
if load_model() is None:
    st.warning("The ML model couldn't be loaded, so only the merchant list is being used.")
gaps = find_balance_gaps(raw)
if not gaps.empty:
    st.warning(f"Your statement has {len(gaps)} balance gap(s), so these totals may be incomplete. See the Upload page.")

numbers = summary(df)
totals = by_category(df)

if totals.empty:
    st.info("No spending found in this statement yet. Check the categories in the table below.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total spent", format_inr(numbers["total"]), help=f"Across {numbers['months']} month(s), after refunds.")
    c2.metric("Average per month", format_inr(numbers["per_month"]))
    c3.metric(
        "Avoidable spend",
        format_inr(numbers["avoidable"]),
        help=f"{', '.join(AVOIDABLE_CATEGORIES)}: spending you could choose to cut.",
    )
    c4.metric(
        "Sent to people & cash",
        format_inr(numbers["transfers_out"]),
        help="P2P transfers and ATM cash. Not counted as spending, because we can't see what it paid for.",
    )
    st.caption(
        f"Avoidable spend is {numbers['avoidable_share']:.0%} of your spending, "
        f"about {format_inr(numbers['avoidable_per_month'])} a month."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Spending by category")
        st.plotly_chart(donut(totals), width="stretch", theme=None, config=PLOT_CONFIG)
    with right:
        st.subheader("Monthly spending")
        trend = monthly_trend(df)
        st.plotly_chart(trend_line(trend), width="stretch", theme=None, config=PLOT_CONFIG)

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 merchants")
        top = top_merchants(df)
        st.plotly_chart(merchant_bars(top), width="stretch", theme=None, config=PLOT_CONFIG)
    with right:
        st.subheader("Recurring payments")
        recurring = recurring_payments(df)
        if recurring.empty:
            st.caption("No steady monthly payments found. These need at least 3 months of history.")
        else:
            st.dataframe(
                pd.DataFrame({
                    "Payee": recurring["payee"].str.title(),
                    "Category": recurring["category"],
                    "Per month": recurring["monthly"].map(format_inr),
                    "Per year": recurring["yearly"].map(format_inr),
                    "Last paid": recurring["last_paid"].dt.strftime("%d %b %Y"),
                }),
                width="stretch",
                hide_index=True,
            )
            st.caption(f"Together these cost about {format_inr(recurring['yearly'].sum())} a year.")

    with st.expander("View chart numbers as a table"):
        left, right = st.columns(2)
        left.dataframe(
            pd.DataFrame({
                "Category": totals.index,
                "Spent": totals.map(format_inr).values,
                "Share": (totals / totals.sum()).map("{:.1%}".format).values,
            }),
            width="stretch",
            hide_index=True,
        )
        right.dataframe(
            pd.DataFrame({
                "Month": [p.strftime("%b %Y") for p in trend.index],
                "Spent": trend.map(format_inr).values,
            }),
            width="stretch",
            hide_index=True,
        )

st.divider()
st.subheader("Check your categories")
st.write("Spotted a wrong category? Change it in the **Category** column and every chart above updates.")

to_check = int(df["needs_review"].sum())
left, right, reset = st.columns([2, 2, 1])
only_review = left.toggle(f"Only show rows to check ({to_check})", value=False, disabled=to_check == 0)
right.toggle("Apply my change to all payments with this payee", value=True, key="apply_to_payee")
reset.button(
    "Undo my changes",
    on_click=reset_edits,
    disabled=not st.session_state["category_overrides"],
    width="stretch",
)

view = df[df["needs_review"]] if only_review else df
editor_key = f"category_editor_{st.session_state['editor_version']}_{only_review}"
st.data_editor(
    pd.DataFrame({
        "date": view["date"],
        "payee": view["payee"].str.title(),
        "debit": view["debit"],
        "credit": view["credit"],
        "category": view["category"],
        "decided_by": view["source"].map(SOURCE_LABELS),
    }).reset_index(drop=True),
    key=editor_key,
    on_change=save_edits,
    args=(editor_key, view.index.tolist()),
    width="stretch",
    height=420,
    hide_index=True,
    disabled=["date", "payee", "debit", "credit", "decided_by"],
    column_config={
        "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
        "payee": st.column_config.TextColumn("Payee"),
        "debit": st.column_config.NumberColumn("Money out ₹", format="%.2f"),
        "credit": st.column_config.NumberColumn("Money in ₹", format="%.2f"),
        "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True),
        "decided_by": st.column_config.TextColumn("Decided by"),
    },
)

if st.button("🗑️ Delete my data"):
    clear_user_data()
    st.rerun()

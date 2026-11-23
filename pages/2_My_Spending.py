"""Spending dashboard: click any chart to filter everything else, drill into a merchant, fix categories."""
from functools import partial
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.categorizer import CATEGORIES, SPENDING_CATEGORIES, load_model
from core.parsers import find_balance_gaps, parse_statement
from core.spending import (
    AVOIDABLE_CATEGORIES,
    apply_overrides,
    by_category,
    category_by_month,
    filter_rows,
    format_inr,
    month_labels,
    payee_payments,
    recurring_payments,
    same_payee_ids,
    top_merchants,
)
from core.ui import clear_user_data, load_categorized, page_header, setup_page

setup_page("My Spending", "📊")

DEMO_FILE = Path(__file__).resolve().parents[1] / "data" / "demo_statement.csv"

# Fixed slot per category, so a color always means the same thing.
SERIES = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"],
}
INK = {
    "light": {"text": "#0b0b0b", "muted": "#52514e", "grid": "#e6e5e0", "surface": "#ffffff", "empty": "#eef1ef", "heat": ["#d9efe5", "#1B7F5C"]},
    "dark": {"text": "#f0efec", "muted": "#c3c2b7", "grid": "#33332f", "surface": "#0e1117", "empty": "#1b2321", "heat": ["#1f5a46", "#5eead4"]},
}
SOURCE_LABELS = {"rule": "App rules", "model": "ML model", "person": "Looks like a person", "fallback": "Best guess", "you": "Your correction"}
EXTRA = {"light": ["#8a8984", "#b9b8b2"], "dark": ["#9d9c95", "#6c6b66"]}

mode = "dark" if st.context.theme.type == "dark" else "light"
colors = dict(zip(SPENDING_CATEGORIES, SERIES[mode] + EXTRA[mode]))
ink = INK[mode]
PLOT_CONFIG = {"displayModeBar": False}


# ---------- filter state ----------
def reset_filters() -> None:
    st.session_state.update(f_cats=[], f_months=[], f_payee=None, f_search="")
    for k in ("ver_month", "ver_merch"):
        st.session_state[k] = st.session_state.get(k, 0) + 1


def toggle(list_key: str, value: str) -> None:
    cur = list(st.session_state.get(list_key) or [])
    st.session_state[list_key] = [c for c in cur if c != value] if value in cur else cur + [value]


def click_month(chart_key: str) -> None:
    pts = st.session_state[chart_key]["selection"]["points"]
    if pts:
        toggle("f_months", pts[0]["x"])
    st.session_state["ver_month"] += 1


def click_merchant(chart_key: str, payees: list[str]) -> None:
    pts = st.session_state[chart_key]["selection"]["points"]
    if pts:
        chosen = payees[pts[0]["point_index"]]
        st.session_state["f_payee"] = None if st.session_state.get("f_payee") == chosen else chosen
    st.session_state["ver_merch"] += 1


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


# ---------- charts ----------
def base_layout(height: int) -> dict:
    return {
        "height": height,
        "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": ink["muted"], "size": 13},
        "hoverlabel": {"bgcolor": ink["surface"], "font": {"color": ink["text"]}, "bordercolor": ink["grid"]},
    }


def _fade(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def category_pie(totals: pd.Series, selected: list[str]) -> go.Figure:
    """Share of spending by category. Hatched slices are avoidable; picked categories are pulled out."""
    totals = totals.sort_values(ascending=False)
    cats = list(totals.index)
    fills = [_fade(colors[c], 0.3 if selected and c not in selected else 1.0) for c in cats]
    fig = go.Figure(go.Pie(
        labels=cats, values=totals.values, hole=0.4, sort=False, direction="clockwise",
        marker={
            "colors": fills,
            "line": {"color": ink["surface"], "width": 2},
            # In a pie the stripes are drawn over `bgcolor`, so every slice needs its colour there too.
            "pattern": {"shape": ["/" if c in AVOIDABLE_CATEGORIES else "" for c in cats], "bgcolor": fills, "size": 7,
                        "solidity": 0.32, "fgcolor": "rgba(255,255,255,.6)"},
        },
        pull=[0.07 if c in selected else 0 for c in cats],
        textinfo="percent", textposition="inside", insidetextorientation="horizontal",
        textfont={"color": "#ffffff", "size": 13},
        customdata=[format_inr(v) for v in totals.values],
        hovertemplate="<b>%{label}</b><br>%{customdata} · %{percent}<extra></extra>",
    ))
    layout = base_layout(330)
    layout["margin"] = {"l": 8, "r": 8, "t": 8, "b": 8}
    fig.update_layout(
        **layout, clickmode="event+select",
        legend={"orientation": "v", "y": 0.5, "x": 1.0, "xanchor": "right", "itemclick": False, "itemdoubleclick": False,
                "font": {"size": 12, "color": ink["text"]}},
        annotations=[{"text": f"<b>{format_inr(totals.sum())}</b><br><span style='font-size:11px'>spent</span>", "showarrow": False,
                      "x": 0.31, "y": 0.5, "xanchor": "center", "yanchor": "middle", "xref": "paper", "yref": "paper",
                      "font": {"size": 15, "color": ink["text"]}}],
    )
    fig.update_traces(domain={"x": [0, 0.62], "y": [0, 1]})
    return fig


def month_columns(matrix: pd.DataFrame, selected: list[str], share_view: bool) -> go.Figure:
    """Stacked columns per month, split by category. Click a column to pick a month."""
    months = list(matrix.index)
    dim = [0.3 if selected and m not in selected else 1.0 for m in months]
    fig = go.Figure()
    for cat in matrix.columns:
        fig.add_bar(
            name=cat, x=months, y=matrix[cat].values, marker={"color": colors[cat], "opacity": dim},
            customdata=[format_inr(v) for v in matrix[cat].values],
            hovertemplate=f"{cat}: %{{customdata}}<extra></extra>",
        )
    layout = base_layout(340)
    layout["margin"] = {"l": 8, "r": 8, "t": 8, "b": 8}
    fig.update_layout(
        **layout, barmode="stack", barnorm="percent" if share_view else None, bargap=0.3,
        hovermode="x unified", clickmode="event+select",
        legend={"orientation": "h", "y": -0.18, "x": 0.5, "xanchor": "center", "font": {"size": 11}},
    )
    fig.update_xaxes(type="category", showgrid=False, linecolor=ink["grid"], automargin=True)
    fig.update_yaxes(gridcolor=ink["grid"], zeroline=False, automargin=True,
                     **({"ticksuffix": "%"} if share_view else {"tickprefix": "₹", "tickformat": "~s"}))
    if not share_view and len(months) > 1:
        avg = float(matrix.sum(axis=1).mean())
        fig.add_hline(y=avg, line={"color": ink["muted"], "dash": "dot", "width": 1.5},
                      annotation_text=f"average {format_inr(avg)}", annotation_position="top left",
                      annotation_font={"color": ink["muted"], "size": 11})
    fig.update_traces(selected={"marker": {"opacity": 1}}, unselected={"marker": {"opacity": 1}})
    return fig


def merchant_bars(top: pd.DataFrame, selected: str | None) -> go.Figure:
    names = top["payee"].str.title()
    dim = [0.3 if selected and p != selected else 1.0 for p in top["payee"]]
    fig = go.Figure(go.Bar(
        x=top["amount"], y=names, orientation="h",
        marker={"color": [colors.get(c, SERIES[mode][0]) for c in top["category"]], "opacity": dim, "cornerradius": 4},
        text=[format_inr(v) for v in top["amount"]], textposition="outside", textfont={"color": ink["text"]}, cliponaxis=False,
        customdata=list(zip(top["category"], top["payments"])),
        hovertemplate="<b>%{y}</b><br>%{text} over %{customdata[1]} payments<br>%{customdata[0]}<br><i>Click for details</i><extra></extra>",
    ))
    layout = base_layout(max(260, 38 * len(top)))
    layout["margin"] = {"l": 8, "r": 76, "t": 8, "b": 8}
    fig.update_layout(**layout, bargap=0.42, showlegend=False, clickmode="event+select")
    fig.update_xaxes(visible=False, rangemode="tozero")
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", linecolor=ink["grid"], automargin=True)
    fig.update_traces(selected={"marker": {"opacity": 1}}, unselected={"marker": {"opacity": 1}})
    return fig


def payee_timeline(pay: pd.DataFrame, color: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=pay["date"], y=pay["amount"], marker={"color": color, "cornerradius": 3},
        customdata=[format_inr(v) for v in pay["amount"]],
        hovertemplate="<b>%{x|%d %b %Y}</b><br>%{customdata}<extra></extra>",
    ))
    layout = base_layout(150)
    layout["margin"] = {"l": 8, "r": 8, "t": 4, "b": 8}
    fig.update_layout(**layout, bargap=0.5)
    fig.update_xaxes(showgrid=False, linecolor=ink["grid"], automargin=True)
    fig.update_yaxes(gridcolor=ink["grid"], zeroline=False, tickprefix="₹", tickformat="~s", automargin=True)
    return fig


# ---------- page ----------
page_header("My Spending", "📊", "Pick filters (or click a month column) to focus every chart. Then drill into a merchant.", step=2)

raw = st.session_state.get("transactions")
if raw is None:
    with st.container(border=True, key="card_empty_spending"):
        st.markdown("#### Nothing to show yet\nUpload your statement, or explore with a fictional student's account.")
        left, right, _ = st.columns([1, 1, 3])
        if left.button("Try the demo", type="primary", width="stretch"):
            st.session_state["transactions"] = parse_statement(DEMO_FILE, "standard")
            st.session_state["source_name"] = "Demo statement"
            st.session_state["use_demo"] = True
            st.rerun()
        if right.button("Upload my statement", width="stretch"):
            st.switch_page("pages/1_Upload.py")
    st.stop()

df = load_categorized()          # categorised once per statement; corrections survive moving between pages

# A new statement means new months and categories: start with clean filters.
if st.session_state.get("f_for") != st.session_state["categorized_for"]:
    st.session_state["f_for"] = st.session_state["categorized_for"]
    for k in ("ver_month", "ver_merch"):
        st.session_state[k] = 0
    st.session_state.update(f_cats=[], f_months=[], f_payee=None, f_search="")

st.caption(f"Showing: {st.session_state.get('source_name', 'statement')}")
if load_model() is None:
    st.warning("The ML model couldn't be loaded, so only the merchant list is being used.")
gaps = find_balance_gaps(raw)
if not gaps.empty:
    st.warning(f"Your statement has {len(gaps)} balance gap(s), so these totals may be incomplete. See the Upload page.")

all_months = month_labels(df)
all_totals = by_category(df)
if all_totals.empty:
    st.info("No spending found in this statement yet. Check the categories in the table at the bottom.")

# ----- filters (charts below write into these too) -----
with st.container(border=True, key="card_filters"):
    f1, f2, f3 = st.columns([3, 3, 1], vertical_alignment="bottom")
    f1.multiselect("Categories", options=list(all_totals.index), key="f_cats", placeholder="All categories",
                   help="Pick one or more categories.")
    f2.multiselect("Months", options=all_months, key="f_months", placeholder="All months",
                   help="Pick one or more, or click a column in the monthly chart.")
    chips = list(st.session_state["f_cats"]) + list(st.session_state["f_months"])
    if st.session_state.get("f_payee"):
        chips.append(st.session_state["f_payee"].title())
    f3.button("Clear all", on_click=reset_filters, disabled=not chips, width="stretch")
    if chips:
        st.caption("Filtering by: " + " · ".join(chips))

cats, months = st.session_state["f_cats"], st.session_state["f_months"]
payee = st.session_state.get("f_payee")
df_m = filter_rows(df, months=months)                          # for the category chart (not by category)
df_c = filter_rows(df, categories=cats)                        # for the monthly chart (not by month)
df_f = filter_rows(df, categories=cats, months=months)         # everything else
totals_m, totals_f = by_category(df_m), by_category(df_f)

# ----- headline numbers for the current selection -----
n_months = max(len(months) or len(all_months), 1)
total = float(totals_f.sum())
avoid = float(totals_f.reindex(AVOIDABLE_CATEGORIES, fill_value=0).sum())
sent = float(df_m.loc[df_m["category"] == "Transfers (P2P)", "debit"].sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total spent", format_inr(total), help=f"Across {n_months} month(s), after refunds.")
c2.metric("Average per month", format_inr(total / n_months))
c3.metric("Avoidable spend", format_inr(avoid), help=f"{', '.join(AVOIDABLE_CATEGORIES)}: spending you could choose to cut.")
c4.metric("Sent to people", format_inr(sent),
          help="P2P transfers and ATM cash. Not counted as spending, because we can't see what it paid for.")
if total:
    top_cat = totals_f.idxmax()
    st.caption(f"{top_cat} is the biggest slice at {totals_f.max() / total:.0%}. "
               f"Avoidable categories are {avoid / total:.0%} of this spending, about {format_inr(avoid / n_months)} a month.")

if df_f.empty or total == 0:
    st.info("Nothing matches these filters.")
else:
    left, right = st.columns(2)
    with left:
        st.subheader("Where it went")
        st.caption("Hatched slices are avoidable. Hover for amounts; use the Categories filter to focus.")
        st.plotly_chart(category_pie(totals_m, cats), width="stretch", theme=None, config=PLOT_CONFIG)
    with right:
        st.subheader("Month by month")
        view = st.segmented_control("Show", ["Amount", "Share of month"], default="Amount", key="month_view",
                                    label_visibility="collapsed")
        matrix = category_by_month(df_c, all_months)
        key = f"month_chart_{st.session_state.get('ver_month', 0)}"
        st.plotly_chart(month_columns(matrix, months, view == "Share of month"), width="stretch", theme=None,
                        config=PLOT_CONFIG, on_select=partial(click_month, key), selection_mode="points", key=key)

    left, right = st.columns(2)
    top = top_merchants(df_f)
    with left:
        st.subheader("Top merchants")
        st.caption("Click a merchant to see every payment to it.")
        key = f"merch_chart_{st.session_state.get('ver_merch', 0)}"
        st.plotly_chart(merchant_bars(top, payee), width="stretch", theme=None, config=PLOT_CONFIG,
                        on_select=partial(click_merchant, key, top["payee"].tolist()), selection_mode="points", key=key)
    with right:
        if payee:
            st.subheader(payee.title())
            pay = payee_payments(df_f, payee)
            if pay.empty:
                st.caption("No payments to this merchant in the current filters.")
            else:
                st.markdown(f"**{format_inr(pay['amount'].sum())}** in total · **{len(pay)}** payments · "
                            f"**{format_inr(pay['amount'].mean())}** on average")
                st.plotly_chart(payee_timeline(pay, colors.get(pay["category"].iloc[0], SERIES[mode][0])),
                                width="stretch", theme=None, config=PLOT_CONFIG)
                st.dataframe(pd.DataFrame({"Date": pay["date"].dt.strftime("%d %b %Y"), "Amount": pay["amount"].map(format_inr),
                                           "Category": pay["category"]}), width="stretch", hide_index=True, height=150)
            st.button("✕ Back to all merchants", on_click=lambda: st.session_state.update(
                f_payee=None, ver_merch=st.session_state.get("ver_merch", 0) + 1))
        else:
            st.subheader("Recurring payments")
            recurring = recurring_payments(df_c)
            if recurring.empty:
                st.caption("No steady monthly payments found. These need at least 3 months of history.")
            else:
                st.dataframe(
                    pd.DataFrame({
                        "Payee": recurring["payee"].str.title(), "Category": recurring["category"],
                        "Per month": recurring["monthly"].map(format_inr), "Per year": recurring["yearly"].map(format_inr),
                        "Last paid": recurring["last_paid"].dt.strftime("%d %b %Y"),
                    }), width="stretch", hide_index=True)
                st.caption(f"Together these cost about {format_inr(recurring['yearly'].sum())} a year.")

    with st.expander("View chart numbers as a table"):
        l, r = st.columns(2)
        l.dataframe(pd.DataFrame({"Category": totals_f.index, "Spent": totals_f.map(format_inr).values,
                                  "Share": (totals_f / totals_f.sum()).map("{:.1%}".format).values}), width="stretch", hide_index=True)
        mm = category_by_month(df_c, all_months).sum(axis=1)
        r.dataframe(pd.DataFrame({"Month": mm.index, "Spent": mm.map(format_inr).values}), width="stretch", hide_index=True)

st.divider()
to_check = int(df["needs_review"].sum())
show_editor = st.session_state.get("show_editor", False)
check_col, next_col = st.columns([1, 1], vertical_alignment="center")
if check_col.button(("Hide category checker" if show_editor else f"Check your categories ({to_check} to review)"),
                    key="toggle_editor"):
    st.session_state["show_editor"] = not show_editor
    st.rerun()
if next_col.button("Next: My Surplus →", type="primary", width="stretch", key="next_surplus"):
    st.switch_page("pages/3_My_Surplus.py")

if st.session_state.get("show_editor", False):
    st.subheader("Check your categories")
    st.write("Spotted a wrong category? Change it in the **Category** column and every chart above updates. "
             "The table follows your filters.")
    left, right, reset = st.columns([2, 2, 1])
    only_review = left.toggle(f"Only show rows to check ({to_check})", value=False, disabled=to_check == 0)
    right.toggle("Apply my change to all payments with this payee", value=True, key="apply_to_payee")
    reset.button("Undo my changes", on_click=reset_edits, disabled=not st.session_state["category_overrides"], width="stretch")
    search = st.text_input("Search payee", key="f_search", placeholder="e.g. swiggy")

    view_rows = filter_rows(df, categories=cats, months=months, payee=payee, search=search)
    if only_review:
        view_rows = view_rows[view_rows["needs_review"]]
    editor_key = f"category_editor_{st.session_state['editor_version']}_{only_review}"
    st.data_editor(
        pd.DataFrame({
            "date": view_rows["date"], "payee": view_rows["payee"].str.title(), "debit": view_rows["debit"],
            "credit": view_rows["credit"], "category": view_rows["category"], "decided_by": view_rows["source"].map(SOURCE_LABELS),
        }).reset_index(drop=True),
        key=editor_key, on_change=save_edits, args=(editor_key, view_rows.index.tolist()),
        width="stretch", height=420, hide_index=True,
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

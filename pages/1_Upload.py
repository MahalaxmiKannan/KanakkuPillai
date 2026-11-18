"""Upload a bank statement (or load the demo) into the session."""
from pathlib import Path

import streamlit as st

from core.parsers import BANKS, StatementParseError, find_balance_gaps, parse_statement, summarize
from core.ui import clear_user_data, setup_page

setup_page("Upload", "📤")

DEMO_FILE = Path(__file__).resolve().parents[1] / "data" / "demo_statement.csv"

st.title("📤 Upload your statement")

st.success(
    "**Privacy:** your file is processed in memory on our server and never saved. "
    "Account numbers and UPI IDs are masked as soon as the file is read. "
    "Use **Delete my data** below to clear everything from this session.",
    icon="🔒",
)

source = st.radio(
    "What would you like to analyse?",
    ["My own statement", "Demo statement (fictional student)"],
    index=1 if st.session_state.get("use_demo") else 0,
    horizontal=True,
)

if source.startswith("Demo"):
    st.session_state["use_demo"] = True
    if st.button("Load demo statement", type="primary"):
        df = parse_statement(DEMO_FILE, "standard")
        st.session_state["transactions"] = df
        st.session_state["source_name"] = "Demo statement"
else:
    st.session_state["use_demo"] = False
    bank = st.selectbox(
        "Your bank's format",
        options=list(BANKS),
        format_func=lambda key: BANKS[key].name,
    )
    st.caption(f"How to get it: {BANKS[bank].note}")
    uploaded = st.file_uploader("Statement file (CSV)", type=["csv"], accept_multiple_files=False)

    if uploaded is not None:
        try:
            df = parse_statement(uploaded, bank)
        except StatementParseError as err:
            st.error(f"Couldn't read that file. {err}")
        else:
            st.session_state["transactions"] = df
            st.session_state["source_name"] = uploaded.name

df = st.session_state.get("transactions")

if df is not None:
    s = summarize(df)
    st.divider()
    st.subheader(f"Loaded: {st.session_state.get('source_name', 'statement')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{s['rows']:,}")
    c2.metric("Period", f"{s['start']:%d %b %y} – {s['end']:%d %b %y}")
    c3.metric("Money in", f"₹{s['total_credit']:,.0f}")
    c4.metric("Money out", f"₹{s['total_debit']:,.0f}")
    gaps = find_balance_gaps(df)
    for g in gaps.itertuples():
        direction = "out" if g.amount < 0 else "in"
        st.warning(
            f"⚠️ Your balance changes by ₹{abs(g.amount):,.2f} between "
            f"{g.from_date:%d %b} and {g.to_date:%d %b} with no transaction explaining it. "
            f"Money {direction} is missing from this file, so totals may be off by this amount. "
            "Try downloading the statement again for those dates."
        )

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "description": st.column_config.TextColumn("Description (masked)", width="large"),
            "payee": st.column_config.TextColumn("Payee"),
            "debit": st.column_config.NumberColumn("Debit ₹", format="%.2f"),
            "credit": st.column_config.NumberColumn("Credit ₹", format="%.2f"),
            "balance": st.column_config.NumberColumn("Balance ₹", format="%.2f"),
        },
    )

    left, right = st.columns([3, 1])
    with left:
        if st.button("Next: see my spending →", type="primary"):
            st.switch_page("pages/2_My_Spending.py")
    with right:
        if st.button("🗑️ Delete my data", width="stretch"):
            clear_user_data()
            st.rerun()
else:
    st.info("No statement loaded yet.")

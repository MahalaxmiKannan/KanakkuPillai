"""My Surplus: income vs essentials vs the rest, and an emergency fund before anything else."""
import streamlit as st

from core.spending import format_inr
from core.surplus import compute_surplus
from core.ui import empty_state, load_categorized, page_header, setup_page

setup_page("My Surplus", "🏦")
page_header("My Surplus", "🏦", "What is left each month, and an emergency fund before anything else.", step=3)

df = load_categorized()
if df is None:
    empty_state("Your surplus is worked out from a statement, so load one first.", ("Go to Upload", "pages/1_Upload.py"))
    st.stop()

st.caption(f"Showing: {st.session_state.get('source_name', 'statement')}")

with st.sidebar:
    st.header("Adjust")
    detected = compute_surplus(df)["income_detected"]
    use_override = st.toggle(
        "Enter my own monthly income",
        value=detected <= 0,
        help="Use this if your income isn't in the statement, or the detected figure is wrong.",
    )
    override = None
    if use_override:
        override = st.number_input("Monthly income (₹)", min_value=0, value=int(detected), step=500)
    irregular = st.toggle("My income is irregular", help="Aims for 6 months of essentials instead of 3.")
    months_target = 6 if irregular else 3
    saved = st.number_input("Emergency savings I already have (₹)", min_value=0, value=0, step=1000)
    count_transfers = st.toggle(
        "Count money I sent to people as spending",
        help="Payments to people aren't counted by default, because the app can't see what they were for. "
        "Turn this on if they were really rent, shared bills or food.",
    )

r = compute_surplus(df, override, months_target, float(saved), count_transfers)
st.session_state["surplus"] = r

if override is None and r["income_detected"] <= 0:
    st.warning("No income was found in this statement. Enter your monthly income in the sidebar.")
if r["months"] < 3:
    st.warning(f"This statement covers only {r['months']} month(s), so these averages are rough.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Income / month", format_inr(r["income"]), help="Detected from the statement unless you entered your own.")
c2.metric("Essentials / month", format_inr(r["essentials"]), help="Bills, groceries, education, health and rent.")
c3.metric("Everything else / month", format_inr(r["discretionary"] + r["transfers_counted"]))
c4.metric("Left over / month", format_inr(r["surplus"]), delta_color="off")

if r["transfers_per_month"] > 0 and not count_transfers:
    st.caption(
        f"You also sent about {format_inr(r['transfers_per_month'])} a month to people, which isn't counted above. "
        "If that was really spending, turn on the sidebar option."
    )

st.divider()
st.subheader("Emergency fund first")
st.write(
    f"A common rule is {months_target} months of essentials set aside before taking any investment risk. "
    f"For you that is **{format_inr(r['emergency_target'])}**."
)
st.progress(r["emergency_progress"], text=f"{format_inr(r['emergency_saved'])} of {format_inr(r['emergency_target'])}")

st.subheader("A safe amount to set aside")
if r["surplus"] <= 0:
    st.warning(
        "Your spending is at or above your income, so there is nothing safe to set aside yet. "
        "My Spending shows which categories are the biggest."
    )
else:
    st.metric("Safe to set aside each month", format_inr(r["safe_to_set_aside"]))
    if r["emergency_gap"] > 0:
        st.write(
            f"Of this, **{format_inr(r['to_emergency_fund'])}** would go to your emergency fund, "
            f"which would be full in about **{r['months_to_fund']:.1f} months**. "
            f"After that, {format_inr(r['safe_to_set_aside'])} a month is free."
        )
    else:
        st.write("Your emergency fund is full, so the whole amount is free to set aside.")
    st.caption("This is simple arithmetic on past spending, not advice on what to do with the money.")

st.page_link("pages/4_Risk_Quiz.py", label="Next: Risk quiz →")

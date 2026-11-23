"""Risk quiz: nine questions, a profile and what it means. No product recommendations."""
import streamlit as st

from core.risk_quiz import QUESTIONS, result
from core.ui import page_header, setup_page

setup_page("Risk Quiz", "🧭")
page_header("Risk Quiz", "🧭", "Nine questions about how you feel about risk. There are no right answers.", step=3)

with st.form("risk_quiz"):
    picks = []
    for i, item in enumerate(QUESTIONS, start=1):
        picks.append(st.radio(f"{i}. {item['q']}", item["options"], index=None, key=f"quiz_{i}"))
    submitted = st.form_submit_button("See my profile", type="primary")

if submitted:
    if any(p is None for p in picks):
        st.error("Please answer every question.")
    else:
        answers = [QUESTIONS[i]["options"].index(p) for i, p in enumerate(picks)]
        st.session_state["risk_result"] = result(answers)

res = st.session_state.get("risk_result")
if res:
    st.divider()
    st.subheader(f"Your profile: {res['profile']}")
    st.caption(f"Score {res['total']} out of {res['max']}")
    st.write(f"**{res['summary']}**")
    st.write(res["meaning"])
    for note in res["notes"]:
        st.warning(note)
    st.caption("A quiz can't know your whole situation. This describes comfort with risk; it doesn't tell you what to buy.")
    st.page_link("pages/4_Learn.py", label="Next: Learn about the options →")

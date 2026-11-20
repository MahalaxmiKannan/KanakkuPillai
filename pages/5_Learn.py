"""Learn the options: plain-language cards. Never uses the user's own numbers or recommends anything."""
from pathlib import Path

import streamlit as st

from core.ui import setup_page

setup_page("Learn", "📚")
st.title("📚 Learn")
st.write("What the common options mean: how risky, how locked-in, how easy to get out of, and how they are taxed.")

CONTENT = Path(__file__).resolve().parents[1] / "content"
cards = sorted(CONTENT.glob("[0-9]_*.md"))

res = st.session_state.get("risk_result")
if res:
    st.caption(f"Your quiz profile was {res['profile']}. The cards below are the same for everyone; they don't change with it.")

for path in cards:
    text = path.read_text(encoding="utf-8")
    title, _, body = text.partition("\n")
    with st.expander(title.lstrip("# ").strip()):
        st.markdown(body.strip())

st.divider()
st.subheader("Spreading your money (diversification)")
st.write(
    "Different options behave differently. Some stay steady and some swing a lot, and they don't all fall at the same time. "
    "Putting everything in one place means one bad outcome hits all of it. "
    "Spreading money across a few kinds of options, and across many companies inside a fund, is how people reduce that risk. "
    "It lowers the chance of a big loss; it doesn't remove it or guarantee a gain."
)
st.caption("This is general information about how investing works. It is not a recommendation to buy anything.")
st.page_link("pages/6_Simulator.py", label="Next: Simulator →")

"""Learn the options as a small page-turning book. Never uses the user's own numbers or recommends anything."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from core.flipbook import DIVERSIFICATION, build_book, load_chapters
from core.ui import page_header, setup_page

setup_page("Learn", "📚")
page_header("Learn", "📚", "Flip through the Money Handbook: what each option means, how risky it is, how locked-in, and how it's taxed.", step=5)

CONTENT = Path(__file__).resolve().parents[1] / "content"
chapters = load_chapters(CONTENT)

res = st.session_state.get("risk_result")
if res:
    st.caption(f"Your quiz profile was {res['profile']}. The book is the same for everyone; it doesn't change with your profile.")

dark = st.context.theme.type == "dark"
components.html(build_book(chapters, dark=dark), height=710, scrolling=False)
st.caption("Tap a page or use Next to turn it. On a computer, the ← → keys work too; on a phone, swipe.")

with st.expander("Prefer a plain list? Read every chapter here"):
    for path in sorted(CONTENT.glob("[0-9]_*.md")):
        title, _, body = path.read_text(encoding="utf-8").partition("\n")
        st.markdown(f"### {title.lstrip('# ').strip()}")
        st.markdown(body.strip())
    st.markdown("### Spreading your money (diversification)")
    st.write(DIVERSIFICATION)

st.caption("This is general information about how investing works. It is not a recommendation to buy anything.")
st.page_link("pages/6_Simulator.py", label="Next: Simulator →")

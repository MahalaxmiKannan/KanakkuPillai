"""Home page of KanakkuPillai: one screen, name + tagline, and the app as a roadmap."""
import streamlit as st
import streamlit.components.v1 as components

from core.roadmap import build_roadmap
from core.ui import setup_page

setup_page("Home", "💰")

# Home only: tighter spacing so everything fits on one screen.
st.markdown(
    """
<style>
  .block-container { padding-top: 1.2rem !important; padding-bottom: 0 !important; }
  .kp-top { display:flex; align-items:flex-end; gap:1rem; margin: .1rem 0 .2rem; }
  .kp-brand { font-size: clamp(2rem, 4.2vw, 3.1rem); font-weight: 800; letter-spacing: -0.03em; line-height: 1;
    background: linear-gradient(90deg, #e11d48, #f5a524 45%, #1B7F5C 80%); background-size: 200% auto;
    -webkit-background-clip: text; background-clip: text; color: transparent; animation: kpShift 8s ease infinite; }
  .kp-tagline { font-size: clamp(1rem, 1.6vw, 1.25rem); font-weight: 600; opacity: .85; margin-top: .35rem; }
  .kp-tagline span { opacity: .7; font-weight: 400; }
  iframe[title="streamlit_components_v1.html"], .stIFrame { display:block; }
  .kp-foot { font-size: .8rem; opacity: .65; text-align: center; margin-top: -.4rem; }
</style>
""",
    unsafe_allow_html=True,
)

left, b1, b2 = st.columns([3.2, 1, 1], vertical_alignment="bottom")
left.markdown(
    '<div class="kp-brand">KanakkuPillai</div>'
    '<div class="kp-tagline">Where does my ₹ go? <span>From wasting it to investing it wisely.</span></div>',
    unsafe_allow_html=True,
)
if b1.button("Upload my statement", type="primary", width="stretch"):
    st.session_state["use_demo"] = False
    st.switch_page("pages/1_Upload.py")
if b2.button("Try the demo", width="stretch"):
    st.session_state["use_demo"] = True
    st.switch_page("pages/1_Upload.py")

components.html(build_roadmap(dark=st.context.theme.type == "dark"), height=450, scrolling=False)

st.markdown(
    '<div class="kp-foot">🔒 Your statement is processed in memory and never saved · '
    "Tap any stop to jump there · The demo uses a fictional student's account</div>",
    unsafe_allow_html=True,
)

"""Home page of KanakkuPillai: one screen, green hero, and the app told as a story the reader moves through."""
import streamlit as st
import streamlit.components.v1 as components

from core.roadmap import build_roadmap
from core.ui import setup_page

setup_page("Home", "💰")

# Home only: a compact version of the green hero so everything fits on one screen.
st.markdown(
    """
<style>
  .block-container { padding-top: 1.1rem !important; padding-bottom: 0 !important; }
  .kp-hero.compact { padding: 1.1rem 1.6rem 1.05rem; margin-bottom: .55rem; border-radius: 24px; }
  .kp-hero.compact h1 { font-size: clamp(2rem, 4vw, 2.8rem); margin: 0; line-height: 1.05; }
  .kp-hero.compact .tag { margin: .15rem 0 0; font-size: clamp(1rem, 1.7vw, 1.3rem); }
  .kp-hero.compact .kp-coin.c1 { top: 18%; } .kp-hero.compact .kp-coin.c2 { top: 52%; right: 14%; }
  @media (max-width: 640px) {
    .kp-hero.compact { padding: .8rem 1.1rem; }
    .kp-hero.compact .kp-coin { display: none; }
    /* keep the two buttons side by side and drop the note, to save height */
    [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .5rem; }
    [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) { display: none; }
  }
</style>
<div class="kp-hero compact">
  <span class="kp-blob b1"></span><span class="kp-blob b2"></span>
  <span class="kp-coin c1">🪙</span><span class="kp-coin c2">🐷</span><span class="kp-coin c3">₹</span>
  <h1>KanakkuPillai</h1>
  <div class="tag">Where does my ₹ go? From wasting it to investing it wisely.</div>
</div>
""",
    unsafe_allow_html=True,
)

b1, b2, note = st.columns([1, 1, 2.4], vertical_alignment="center")
if b1.button("Upload my statement", type="primary", width="stretch"):
    st.session_state["use_demo"] = False
    st.switch_page("pages/1_Upload.py")
if b2.button("Try the demo", width="stretch"):
    st.session_state["use_demo"] = True
    st.switch_page("pages/1_Upload.py")
note.caption("🔒 Processed in memory, never saved. The demo uses a fictional student's account.")

components.html(build_roadmap(dark=st.context.theme.type == "dark"), height=450, scrolling=False)

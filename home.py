"""Home page of KanakkuPillai: a scroll-driven story of one month of money, from "where did it go?" to a plan."""
import streamlit as st

from core.scrollstory import build_story, story_data
from core.ui import setup_page

setup_page("Home", "💰")

# Home only: full-bleed, no extra spacing, and the scene carries its own disclaimer pill,
# so the standard banner (which would scroll away) is hidden here.
st.markdown(
    """
<style>
  .block-container { max-width: none !important; padding: 0 !important; }
  [data-testid="stMainBlockContainer"] { padding: 0 !important; }
  [data-testid="stVerticalBlock"] { gap: 0 !important; }
  .kp-disclaimer { display: none !important; }
  [data-testid="stElementContainer"]:has(> [data-testid="stMarkdownContainer"] .kp-disclaimer) { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def _story() -> str:
    return build_story(story_data())


st.html(_story(), unsafe_allow_javascript=True)

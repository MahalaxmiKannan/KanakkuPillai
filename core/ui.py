"""Shared UI pieces used by every page."""
import pandas as pd
import streamlit as st

APP_NAME = "KanakkuPillai"


STEPS = [
    ("Upload", "pages/1_Upload.py"),
    ("Spending", "pages/2_My_Spending.py"),
    ("Surplus", "pages/3_My_Surplus.py"),
    ("Risk quiz", "pages/4_Risk_Quiz.py"),
    ("Learn", "pages/5_Learn.py"),
    ("Simulator", "pages/6_Simulator.py"),
    ("Scam check", "pages/7_Scam_Checker.py"),
]

# Colours use rgba / currentColor so everything works in light and dark themes.
CSS = """
<style>
  .block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }
  header[data-testid="stHeader"] { background: transparent; }
  footer { visibility: hidden; }
  h1 { font-weight: 750; letter-spacing: -0.02em; }
  h2, h3 { font-weight: 650; letter-spacing: -0.01em; }

  /* metric cards */
  [data-testid="stMetric"] {
    background: rgba(128,128,128,0.07);
    border: 1px solid rgba(128,128,128,0.22);
    border-radius: 14px;
    padding: 14px 16px;
  }
  [data-testid="stMetricLabel"] { opacity: 0.75; }
  [data-testid="stMetricValue"] { font-weight: 700; }

  /* bordered containers become soft cards */
  [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }

  /* buttons */
  .stButton > button, [data-testid="stPageLink"] a { border-radius: 10px; font-weight: 600; }

  /* expanders */
  [data-testid="stExpander"] { border-radius: 12px; }

  /* tidy, slim disclaimer */
  .kp-disclaimer {
    display: flex; gap: 10px; align-items: flex-start;
    border: 1px solid rgba(128,128,128,0.22);
    border-left: 4px solid #1B7F5C;
    border-radius: 10px; padding: 8px 14px; margin-bottom: 1.2rem;
    font-size: 0.86rem; line-height: 1.4; background: rgba(27,127,92,0.07);
  }

  /* step tracker */
  .kp-steps { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 0.9rem 0; }
  .kp-step {
    font-size: 0.78rem; padding: 3px 11px; border-radius: 999px;
    border: 1px solid rgba(128,128,128,0.3); opacity: 0.7;
  }
  .kp-step.done { opacity: 0.9; border-color: #1B7F5C; }
  .kp-step.now { background: #1B7F5C; border-color: #1B7F5C; color: #fff; opacity: 1; font-weight: 600; }
  .kp-sub { font-size: 1.05rem; opacity: 0.78; margin-top: -0.4rem; margin-bottom: 1.2rem; }

  /* home */
  .kp-hero { padding: 1.4rem 0 0.4rem 0; }
  .kp-hero h1 { font-size: 3rem; margin-bottom: 0.2rem; }
  .kp-hero .tag { font-size: 1.3rem; font-weight: 600; color: #1B7F5C; margin-bottom: 0.6rem; }
  .kp-hero p { font-size: 1.08rem; max-width: 46rem; opacity: 0.85; }
  .kp-card-icon { font-size: 1.7rem; line-height: 1; margin-bottom: 0.35rem; }
  .kp-card-title { font-weight: 650; font-size: 1.05rem; margin-bottom: 0.2rem; }
  .kp-card-text { font-size: 0.93rem; opacity: 0.8; }
  .kp-num {
    display: inline-flex; width: 28px; height: 28px; border-radius: 50%;
    background: #1B7F5C; color: #fff; font-weight: 700; align-items: center;
    justify-content: center; margin-bottom: 0.4rem;
  }
  @media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem; }
    .kp-hero h1 { font-size: 2.2rem; }
    .kp-hero .tag { font-size: 1.1rem; }
  }
</style>
"""


def setup_page(title: str, icon: str = "💰") -> None:
    """Set the browser tab title and icon, apply the shared look, then show the disclaimer.

    Call this as the FIRST Streamlit command on every page.
    """
    st.set_page_config(
        page_title=f"{title} · {APP_NAME}",
        page_icon=icon,
        layout="wide",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    show_disclaimer()


def page_header(title: str, icon: str = "", subtitle: str = "", step: int | None = None) -> None:
    """Title, optional one-line subtitle, and a tracker showing where you are in the journey.

    step is 1-based and matches STEPS.
    """
    if step is not None:
        pills = []
        for i, (name, _) in enumerate(STEPS, start=1):
            state = "now" if i == step else "done" if i < step else ""
            pills.append(f'<span class="kp-step {state}">{i}. {name}</span>')
        st.markdown(f'<div class="kp-steps">{"".join(pills)}</div>', unsafe_allow_html=True)
    st.title(f"{icon} {title}".strip())
    if subtitle:
        st.markdown(f'<div class="kp-sub">{subtitle}</div>', unsafe_allow_html=True)


def empty_state(message: str, primary: tuple[str, str] | None = None, secondary: tuple[str, str] | None = None) -> None:
    """A friendly 'nothing here yet' card with up to two buttons: (label, page path)."""
    with st.container(border=True):
        st.markdown(f"#### Nothing to show yet\n{message}")
        cols = st.columns([1, 1, 3])
        for col, action, kind in ((cols[0], primary, "primary"), (cols[1], secondary, "secondary")):
            if action and col.button(action[0], type=kind, width="stretch", key=f"empty_{action[1]}"):
                st.switch_page(action[1])


def coming_soon(blurb: str, day: str) -> None:
    """Placeholder body for pages that aren't built yet."""
    with st.container(border=True):
        st.markdown(f"#### Coming soon ({day})\n{blurb}")


def clear_user_data() -> None:
    """Forget the statement, its categories and the user's corrections."""
    st.session_state.clear()


def show_disclaimer() -> None:
    """The banner that reminds users this is not financial advice."""
    st.markdown(
        '<div class="kp-disclaimer"><span>ℹ️</span><span><b>Educational tool only, not investment advice.</b> '
        "Your data is processed in memory and never saved.</span></div>",
        unsafe_allow_html=True,
    )


def load_categorized() -> "pd.DataFrame | None":
    """The user's categorised statement with their corrections applied, or None if none is loaded.

    Categorises once per statement and keeps corrections in session state, so
    My Spending and My Surplus always agree.
    """
    from core.categorizer import categorize
    from core.spending import apply_overrides

    raw = st.session_state.get("transactions")
    if raw is None:
        return None
    fingerprint = int(pd.util.hash_pandas_object(raw[["date", "description", "debit", "credit"]], index=False).sum())
    if st.session_state.get("categorized_for") != fingerprint:
        st.session_state["categorized"] = categorize(raw)
        st.session_state["categorized_for"] = fingerprint
        st.session_state["category_overrides"] = {}
        st.session_state["editor_version"] = 0
    return apply_overrides(st.session_state["categorized"], st.session_state["category_overrides"])

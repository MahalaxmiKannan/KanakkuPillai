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
  :root {
    --kp-green: #1B7F5C; --kp-teal: #14b8a6; --kp-amber: #f5a524;
    --kp-line: rgba(128,128,128,0.22); --kp-soft: rgba(128,128,128,0.06);
  }
  .block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }
  header[data-testid="stHeader"] { background: transparent; }
  footer { visibility: hidden; }
  h1 { font-weight: 800; letter-spacing: -0.025em; }
  h2, h3 { font-weight: 700; letter-spacing: -0.015em; }

  /* motion */
  @keyframes kpRise { from { opacity: 0; transform: translateY(18px) scale(.985); } to { opacity: 1; transform: none; } }
  @keyframes kpFloat { 0%,100% { transform: translateY(0) rotate(0); } 50% { transform: translateY(-14px) rotate(8deg); } }
  @keyframes kpShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
  @keyframes kpPulse { 0% { box-shadow: 0 0 0 0 rgba(27,127,92,.45); } 70% { box-shadow: 0 0 0 9px rgba(27,127,92,0); } 100% { box-shadow: 0 0 0 0 rgba(27,127,92,0); } }
  @keyframes kpShine { from { transform: translateX(-120%) skewX(-20deg); } to { transform: translateX(260%) skewX(-20deg); } }

  /* everything slides in, columns one after another */
  [data-testid="stMetric"], [class*="st-key-card_"], [data-testid="stExpander"],
  [data-testid="stPlotlyChart"], .kp-hero, .kp-sub, .kp-steps {
    animation: kpRise .6s cubic-bezier(.2,.8,.2,1) both;
  }
  [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"],
  [data-testid="stColumn"]:nth-child(2) [class*="st-key-card_"] { animation-delay: .08s; }
  [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"],
  [data-testid="stColumn"]:nth-child(3) [class*="st-key-card_"] { animation-delay: .16s; }
  [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"],
  [data-testid="stColumn"]:nth-child(4) [class*="st-key-card_"] { animation-delay: .24s; }

  /* metric cards: glassy, coloured top edge, lift on hover */
  [data-testid="stMetric"] {
    position: relative; overflow: hidden;
    background: linear-gradient(160deg, rgba(27,127,92,.10), var(--kp-soft) 55%);
    border: 1px solid var(--kp-line); border-radius: 18px; padding: 16px 18px;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
  }
  [data-testid="stMetric"]::before {
    content: ""; position: absolute; inset: 0 0 auto 0; height: 3px;
    background: linear-gradient(90deg, var(--kp-green), var(--kp-teal), var(--kp-amber));
  }
  [data-testid="stMetric"]:hover { transform: translateY(-4px); border-color: rgba(27,127,92,.55); box-shadow: 0 14px 30px -14px rgba(27,127,92,.55); }
  [data-testid="stMetricLabel"] { opacity: .75; text-transform: uppercase; letter-spacing: .04em; font-size: .78rem; }
  [data-testid="stMetricValue"] { font-weight: 800; }

  /* cards: lift, glow and slight tilt on hover; press-in on tap */
  [class*="st-key-card_"] {
    border-radius: 20px !important;
    transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s ease, border-color .28s ease;
  }
  [class*="st-key-card_"]:hover {
    transform: translateY(-6px) rotate(-.25deg);
    border-color: rgba(27,127,92,.6) !important;
    box-shadow: 0 22px 40px -22px rgba(27,127,92,.6), 0 0 0 1px rgba(27,127,92,.15);
  }
  [class*="st-key-card_"]:active { transform: translateY(-2px) scale(.985); }

  /* buttons: moving gradient, shine sweep, press-in */
  .stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stPageLink"] a {
    border-radius: 12px; font-weight: 650; transition: transform .15s ease, box-shadow .2s ease;
  }
  .stButton > button:active, [data-testid="stFormSubmitButton"] > button:active, [data-testid="stPageLink"] a:active { transform: scale(.95); }
  .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    position: relative; overflow: hidden; border: 0;
    background: linear-gradient(120deg, var(--kp-green), var(--kp-teal), var(--kp-green));
    background-size: 200% 200%; animation: kpShift 6s ease infinite;
    box-shadow: 0 10px 22px -12px rgba(27,127,92,.9);
  }
  .stButton > button[kind="primary"]::after, [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]::after {
    content: ""; position: absolute; top: 0; left: 0; width: 40%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,.45), transparent);
    transform: translateX(-120%) skewX(-20deg);
  }
  .stButton > button[kind="primary"]:hover::after,
  [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover::after { animation: kpShine .8s ease; }
  .stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 16px 28px -12px rgba(27,127,92,.95); }
  [data-testid="stPageLink"] a:hover { background: rgba(27,127,92,.10); }

  /* expanders and quiz answers as tappable tiles */
  [data-testid="stExpander"] { border-radius: 16px; transition: box-shadow .25s ease; }
  [data-testid="stExpander"]:hover { box-shadow: 0 10px 26px -18px rgba(27,127,92,.7); }
  [role="radiogroup"] label {
    border: 1px solid var(--kp-line); border-radius: 12px; padding: 6px 12px; margin: 3px 0;
    transition: background .2s ease, border-color .2s ease, transform .15s ease;
  }
  [role="radiogroup"] label:hover { border-color: rgba(27,127,92,.6); background: rgba(27,127,92,.07); transform: translateX(3px); }
  [role="radiogroup"] label:has(input:checked) { border-color: var(--kp-green); background: rgba(27,127,92,.13); }

  /* disclaimer */
  .kp-disclaimer {
    display: flex; gap: 10px; align-items: flex-start;
    border: 1px solid var(--kp-line); border-left: 4px solid var(--kp-green);
    border-radius: 12px; padding: 8px 14px; margin-bottom: 1.2rem;
    font-size: .86rem; line-height: 1.4; background: rgba(27,127,92,.07);
  }

  /* step tracker: ticks for done steps, pulsing "you are here" */
  .kp-steps { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 1rem 0; }
  .kp-step { font-size: .78rem; padding: 4px 12px; border-radius: 999px; border: 1px solid var(--kp-line); opacity: .65; transition: opacity .2s, transform .2s; }
  .kp-step:hover { opacity: 1; transform: translateY(-2px); }
  .kp-step.done { opacity: .95; border-color: var(--kp-green); background: rgba(27,127,92,.08); }
  .kp-step.done::before { content: "✓ "; color: var(--kp-green); font-weight: 700; }
  .kp-step.now { background: linear-gradient(120deg, var(--kp-green), var(--kp-teal)); border-color: transparent; color: #fff; opacity: 1; font-weight: 650; animation: kpPulse 2s infinite; }
  .kp-sub { font-size: 1.05rem; opacity: .78; margin-top: -.4rem; margin-bottom: 1.2rem; }

  /* home hero: animated gradient, glowing blobs, floating coins */
  .kp-hero {
    position: relative; overflow: hidden; border-radius: 28px; padding: 2.6rem 2.4rem 2.2rem;
    color: #fff; margin-bottom: 1.2rem;
    background: linear-gradient(125deg, #0f5c43, #1B7F5C, #14b8a6, #0f766e);
    background-size: 300% 300%; animation: kpRise .7s ease both, kpShift 14s ease infinite;
    box-shadow: 0 30px 60px -30px rgba(15,92,67,.8);
  }
  .kp-hero h1 { font-size: 3.1rem; margin: 0 0 .2rem 0; color: #fff; padding: 0; position: relative; z-index: 1; }
  .kp-hero .tag {
    font-size: 1.35rem; font-weight: 700; margin-bottom: .7rem; position: relative; z-index: 1;
    background: linear-gradient(90deg, #fff7d6, #f5a524); -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .kp-hero p { font-size: 1.08rem; max-width: 36rem; opacity: .92; margin: 0; position: relative; z-index: 1; color: #fff; }
  .kp-hero .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1.1rem; position: relative; z-index: 1; }
  .kp-hero .chip { font-size: .8rem; padding: 4px 12px; border-radius: 999px; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28); backdrop-filter: blur(4px); }
  .kp-coin { position: absolute; font-size: 2.4rem; opacity: .9; animation: kpFloat 6s ease-in-out infinite; pointer-events: none; }
  .kp-coin.c1 { right: 6%; top: 14%; }
  .kp-coin.c2 { right: 7%; top: 64%; font-size: 1.8rem; animation-delay: -2s; }
  .kp-coin.c3 { right: 29%; top: 12%; font-size: 1.6rem; animation-delay: -4s; opacity: .75; font-weight: 800; }
  .kp-blob { position: absolute; border-radius: 50%; filter: blur(40px); opacity: .45; pointer-events: none; }
  .kp-blob.b1 { width: 260px; height: 260px; background: #f5a524; right: -60px; bottom: -90px; }
  .kp-blob.b2 { width: 200px; height: 200px; background: #7c5cff; right: 24%; top: -110px; opacity: .3; }

  /* home cards */
  .kp-card-icon {
    font-size: 1.6rem; width: 52px; height: 52px; border-radius: 16px; display: flex; align-items: center; justify-content: center;
    background: linear-gradient(140deg, rgba(27,127,92,.18), rgba(20,184,166,.10)); margin-bottom: .6rem;
    transition: transform .35s cubic-bezier(.2,.8,.2,1);
  }
  [class*="st-key-card_"]:hover .kp-card-icon { transform: scale(1.12) rotate(-8deg); }
  .kp-card-title { font-weight: 700; font-size: 1.06rem; margin-bottom: .25rem; }
  .kp-card-text { font-size: .93rem; opacity: .8; }
  .kp-num {
    display: inline-flex; width: 34px; height: 34px; border-radius: 12px;
    background: linear-gradient(140deg, var(--kp-green), var(--kp-teal)); color: #fff; font-weight: 800;
    align-items: center; justify-content: center; margin-bottom: .55rem; box-shadow: 0 8px 16px -8px rgba(27,127,92,.9);
  }

  @media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem; }
    .kp-hero { padding: 1.8rem 1.3rem; border-radius: 22px; }
    .kp-hero h1 { font-size: 2.1rem; }
    .kp-hero .tag { font-size: 1.1rem; }
    .kp-coin.c3, .kp-blob.b2 { display: none; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
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
    with st.container(border=True, key=f"card_empty_{message[:12]}"):
        st.markdown(f"#### Nothing to show yet\n{message}")
        cols = st.columns([1, 1, 3])
        for col, action, kind in ((cols[0], primary, "primary"), (cols[1], secondary, "secondary")):
            if action and col.button(action[0], type=kind, width="stretch", key=f"empty_{action[1]}"):
                st.switch_page(action[1])


def coming_soon(blurb: str, day: str) -> None:
    """Placeholder body for pages that aren't built yet."""
    with st.container(border=True, key="card_soon"):
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

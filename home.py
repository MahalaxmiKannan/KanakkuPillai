"""Home page of KanakkuPillai."""
import streamlit as st

from core.ui import setup_page

setup_page("Home", "💰")

st.markdown(
    """
<div class="kp-hero">
  <h1>💰 KanakkuPillai</h1>
  <div class="tag">Where does my ₹ go?</div>
  <p>See where your money goes, how much you can safely set aside, what the common savings and
  investment options really mean, and how to spot an investment scam. Made for people starting out.</p>
</div>
""",
    unsafe_allow_html=True,
)

cta1, cta2, _ = st.columns([1, 1, 2])
if cta1.button("Upload my statement", type="primary", width="stretch"):
    st.session_state["use_demo"] = False
    st.switch_page("pages/1_Upload.py")
if cta2.button("Try the demo", width="stretch"):
    st.session_state["use_demo"] = True
    st.switch_page("pages/1_Upload.py")
st.caption("The demo uses a fictional student's account, so you can look around without sharing anything.")

st.markdown("&nbsp;", unsafe_allow_html=True)
st.subheader("How it works")
steps = [
    ("1", "Add a statement", "Upload a bank statement or load the demo. Account numbers and UPI IDs are masked straight away."),
    ("2", "See the picture", "Your spending is sorted into categories. Fix any that are wrong and every chart updates."),
    ("3", "Learn what to do next", "Find a safe amount to set aside, take a short quiz, and read plain-language guides."),
]
for col, (num, title, text) in zip(st.columns(3), steps):
    with col.container(border=True):
        st.markdown(
            f'<div class="kp-num">{num}</div><div class="kp-card-title">{title}</div>'
            f'<div class="kp-card-text">{text}</div>',
            unsafe_allow_html=True,
        )

st.markdown("&nbsp;", unsafe_allow_html=True)
st.subheader("What's inside")
tiles = [
    ("📊", "My Spending", "Categories, monthly trend, top merchants and subscriptions.", "pages/2_My_Spending.py"),
    ("🏦", "My Surplus", "Income, essentials and an emergency fund before anything else.", "pages/3_My_Surplus.py"),
    ("🧭", "Risk Quiz", "Nine questions about how you feel about risk.", "pages/4_Risk_Quiz.py"),
    ("📚", "Learn", "Savings, FD, RD, PPF, index funds, gold and NPS explained.", "pages/5_Learn.py"),
    ("📈", "Simulator", "A range of possible outcomes for a monthly SIP. Coming soon.", "pages/6_Simulator.py"),
    ("🚨", "Scam Checker", "Paste a message and see its red flags. Coming soon.", "pages/7_Scam_Checker.py"),
]
for row in (tiles[:3], tiles[3:]):
    for col, (icon, title, text, page) in zip(st.columns(3), row):
        with col.container(border=True):
            st.markdown(
                f'<div class="kp-card-icon">{icon}</div><div class="kp-card-title">{title}</div>'
                f'<div class="kp-card-text">{text}</div>',
                unsafe_allow_html=True,
            )
            st.page_link(page, label="Open →")

st.markdown("&nbsp;", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("🔒 **Your privacy.** Your file is processed in memory on the server and never saved. "
                "Nothing here connects to your bank, and you can clear everything with **Delete my data**.")
    st.markdown("⚖️ **Not advice.** This app explains and shows; it never tells you to buy a particular stock, fund or scheme.")

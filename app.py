"""Entry point: declares the pages so the sidebar shows clean names."""
import streamlit as st

pages = [
    st.Page("home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Upload.py", url_path="upload", title="Upload", icon="📤"),
    st.Page("pages/2_My_Spending.py", url_path="my-spending", title="My Spending", icon="📊"),
    st.Page("pages/3_Risk_Quiz.py", url_path="risk-quiz", title="Risk Quiz", icon="🧭"),
    st.Page("pages/4_Learn.py", url_path="learn", title="Learn", icon="📚"),
    st.Page("pages/5_My_Surplus.py", url_path="my-surplus", title="My Surplus", icon="🏦"),
    st.Page("pages/6_Simulator.py", url_path="simulator", title="Simulator", icon="📈"),
    st.Page("pages/7_Scam_Checker.py", url_path="scam-checker", title="Scam Checker", icon="🚨"),
    st.Page("pages/8_About.py", url_path="about", title="About", icon="ℹ️"),
]
st.navigation(pages).run()

"""Entry point: declares the pages so the sidebar shows clean names."""
import streamlit as st

pages = [
    st.Page("home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Upload.py", title="Upload", icon="📤"),
    st.Page("pages/2_My_Spending.py", title="My Spending", icon="📊"),
    st.Page("pages/3_My_Surplus.py", title="My Surplus", icon="🏦"),
    st.Page("pages/4_Risk_Quiz.py", title="Risk Quiz", icon="🧭"),
    st.Page("pages/5_Learn.py", title="Learn", icon="📚"),
    st.Page("pages/6_Simulator.py", title="Simulator", icon="📈"),
    st.Page("pages/7_Scam_Checker.py", title="Scam Checker", icon="🚨"),
    st.Page("pages/8_About.py", title="About", icon="ℹ️"),
]
st.navigation(pages).run()

"""Home page of KanakkuPillai."""
import streamlit as st

from core.ui import setup_page

setup_page("Home", "🏠")

st.title("💰 KanakkuPillai")
st.subheader("Where does my ₹ go?")
st.write(
    "Upload your bank statement to see where your money goes, "
    "how much you can safely save, and how to spot investment scams."
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Upload my statement", type="primary", width="stretch"):
        st.session_state["use_demo"] = False
        st.switch_page("pages/1_Upload.py")

with col2:
    if st.button("Try the demo", width="stretch"):
        st.session_state["use_demo"] = True
        st.switch_page("pages/1_Upload.py")
import streamlit as st

from core.ui import coming_soon, page_header, setup_page

setup_page("Simulator", "📈")

page_header("Simulator", "📈", "A range of possible outcomes for a monthly SIP, never a prediction.", step=6)
coming_soon("You will pick a monthly amount and a number of years, and see best, middle and worst cases using real Nifty 50 history.", "Day 4")
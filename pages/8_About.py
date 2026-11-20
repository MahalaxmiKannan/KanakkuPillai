import streamlit as st

from core.ui import coming_soon, page_header, setup_page

setup_page("About", "ℹ️")

page_header("About", "ℹ️", "How the models work, how well they do, and what they cannot do.")
coming_soon("How the categoriser and scam detector work, their real test results, and their limits.", "Day 6")
import streamlit as st

from core.ui import coming_soon, page_header, setup_page


setup_page("Scam Checker", "🚨")

page_header("Scam Checker", "🚨", "Paste a message and see which red flags it shows, and why.", step=7)
coming_soon("Paste a suspicious message and get a low, medium or high risk level with the exact phrases that raised it.", "Day 5")
"""Shared UI pieces used by every page."""
import streamlit as st

APP_NAME = "KanakkuPillai"


def setup_page(title: str, icon: str = "💰") -> None:
    """Set the browser tab title and icon, then show the disclaimer.

    Call this as the FIRST Streamlit command on every page.
    """
    st.set_page_config(
        page_title=f"{title} · {APP_NAME}",
        page_icon=icon,
        layout="wide",
    )
    show_disclaimer()


def clear_user_data() -> None:
    """Forget the statement, its categories and the user's corrections."""
    st.session_state.clear()


def show_disclaimer() -> None:
    """The banner that reminds users this is not financial advice."""
    st.info(
        "**Educational tool only, not investment advice.** "
        "Your data is processed in memory and never saved.",
        icon="ℹ️",
    )
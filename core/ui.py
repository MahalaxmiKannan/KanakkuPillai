"""Shared UI pieces used by every page."""
import pandas as pd
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

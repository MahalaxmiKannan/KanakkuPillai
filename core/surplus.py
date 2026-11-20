"""Surplus maths: income minus spending, an emergency-fund target, and a safe amount to set aside.

No Streamlit here, so it's easy to test.
"""
from __future__ import annotations

import pandas as pd

from core.categorizer import INCOME, TRANSFERS
from core.spending import by_category, month_count

# Things you still pay for in a bad month. Rent counts as essential.
ESSENTIAL_CATEGORIES = ["Bills & recharge", "Groceries", "Education", "Health", "Rent"]


def detected_income(df: pd.DataFrame) -> float:
    """Average monthly income found in the statement (rows categorised as Income)."""
    months = max(month_count(df), 1)
    return float(df.loc[df["category"] == INCOME, "credit"].sum()) / months


def compute_surplus(
    df: pd.DataFrame,
    income_override: float | None = None,
    emergency_months: int = 3,
    emergency_saved: float = 0.0,
    count_transfers: bool = False,
) -> dict:
    """Monthly picture: income, essentials, discretionary, surplus and emergency fund.

    count_transfers=True treats money sent to people as spending, for users whose
    P2P payments are really shared bills or rent.
    """
    months = max(month_count(df), 1)
    totals = by_category(df)
    essentials = float(totals.reindex(ESSENTIAL_CATEGORIES, fill_value=0).sum()) / months
    discretionary = float(totals.sum()) / months - essentials
    p2p = df[df["category"] == TRANSFERS]
    net_sent = max(float(p2p["debit"].sum() - p2p["credit"].sum()), 0.0)
    transfers = net_sent / months if count_transfers else 0.0

    detected = detected_income(df)
    income = detected if income_override is None else float(income_override)
    spend = essentials + discretionary + transfers
    surplus = income - spend

    target = emergency_months * essentials
    gap = max(target - emergency_saved, 0.0)
    safe = max(surplus, 0.0)
    to_fund = min(safe, gap)                       # the emergency fund comes first
    return {
        "months": months,
        "income": income,
        "income_detected": detected,
        "essentials": essentials,
        "discretionary": discretionary,
        "transfers_counted": transfers,
        "transfers_per_month": net_sent / months,
        "spend": spend,
        "surplus": surplus,
        "emergency_target": target,
        "emergency_saved": float(emergency_saved),
        "emergency_progress": min(emergency_saved / target, 1.0) if target > 0 else 1.0,
        "emergency_gap": gap,
        "safe_to_set_aside": safe,
        "to_emergency_fund": to_fund,
        "left_after_fund": safe - to_fund,
        "months_to_fund": (gap / to_fund) if to_fund > 0 and gap > 0 else 0.0,
    }

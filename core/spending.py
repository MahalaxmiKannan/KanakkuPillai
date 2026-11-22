"""Numbers behind the My Spending page. No Streamlit here, so it's easy to test."""
from __future__ import annotations

import pandas as pd

from core.categorizer import SPENDING_CATEGORIES, TRANSFERS

AVOIDABLE_CATEGORIES = ["Food & dining", "Shopping", "Subscriptions"]


def format_inr(amount: float) -> str:
    """Indian digit grouping: 105570 -> ₹1,05,570."""
    sign = "-" if amount < 0 else ""
    digits = str(int(round(abs(amount))))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"{sign}₹{digits}"


def apply_overrides(df: pd.DataFrame, overrides: dict[int, str]) -> pd.DataFrame:
    """Replace categories with the user's corrections, keyed by row index."""
    out = df.copy()
    for txn_id, category in overrides.items():
        if txn_id in out.index:
            out.loc[txn_id, ["category", "source", "needs_review"]] = [category, "you", False]
    return out


def same_payee_ids(df: pd.DataFrame, txn_id: int) -> list[int]:
    """Rows with the same payee and direction (money out or in) as this row."""
    row = df.loc[txn_id]
    same = (df["payee"] == row["payee"]) & ((df["debit"] > 0) == (row["debit"] > 0))
    return df.index[same].tolist()


def _spending(df: pd.DataFrame) -> pd.DataFrame:
    """Spending rows with refunds netted off."""
    rows = df[df["category"].isin(SPENDING_CATEGORIES)].copy()
    rows["amount"] = rows["debit"] - rows["credit"]
    return rows


def month_count(df: pd.DataFrame) -> int:
    """Calendar months covered by the statement, including quiet ones."""
    if df.empty:
        return 0
    return len(pd.period_range(df["date"].min(), df["date"].max(), freq="M"))


def by_category(df: pd.DataFrame) -> pd.Series:
    """Spend per category, always in the same order so colors stay put."""
    totals = _spending(df).groupby("category")["amount"].sum().clip(lower=0)
    return totals.reindex(SPENDING_CATEGORIES).dropna().loc[lambda s: s > 0]


def monthly_trend(df: pd.DataFrame) -> pd.Series:
    """Total spend per month; months with no spending show as 0."""
    if df.empty:
        return pd.Series(dtype=float)
    rows = _spending(df)
    months = pd.period_range(df["date"].min(), df["date"].max(), freq="M")
    totals = rows.groupby(rows["date"].dt.to_period("M"))["amount"].sum()
    return totals.reindex(months, fill_value=0.0).clip(lower=0)


def top_merchants(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Largest payees by spend: payee, amount, payments, category."""
    rows = _spending(df)
    if rows.empty:
        return pd.DataFrame(columns=["payee", "amount", "payments", "category"])
    grouped = rows.groupby("payee").agg(
        amount=("amount", "sum"),
        payments=("amount", "size"),
        category=("category", "first"),
    )
    grouped = grouped[grouped["amount"] > 0].sort_values("amount", ascending=False)
    return grouped.head(n).reset_index()


def recurring_payments(df: pd.DataFrame) -> pd.DataFrame:
    """Payments of a steady amount, about once a month, for 3+ months."""
    columns = ["payee", "category", "monthly", "months", "last_paid", "yearly"]
    found = []
    for payee, rows in df[df["debit"] > 0].groupby("payee"):
        months = rows["date"].dt.to_period("M").nunique()
        typical = rows["debit"].median()
        steady = rows["debit"].between(typical * 0.8, typical * 1.2).all()
        if months >= 3 and len(rows) <= months * 1.5 and steady and payee != "unknown":
            found.append({
                "payee": payee,
                "category": rows["category"].iloc[-1],
                "monthly": float(typical),
                "months": months,
                "last_paid": rows["date"].max(),
                "yearly": float(typical) * 12,
            })
    result = pd.DataFrame(found, columns=columns)
    return result.sort_values("monthly", ascending=False).reset_index(drop=True)


def summary(df: pd.DataFrame) -> dict:
    """Headline numbers for the top of the page."""
    months = max(month_count(df), 1)
    total = float(by_category(df).sum())
    categories = by_category(df)
    avoidable = float(categories.reindex(AVOIDABLE_CATEGORIES, fill_value=0).sum())
    sent = float(df.loc[df["category"] == TRANSFERS, "debit"].sum())
    return {
        "total": total,
        "per_month": total / months,
        "avoidable": avoidable,
        "avoidable_per_month": avoidable / months,
        "avoidable_share": avoidable / total if total else 0.0,
        "transfers_out": sent,
        "months": months,
    }


def month_labels(df: pd.DataFrame) -> list[str]:
    """Every calendar month the statement covers, oldest first, like 'May 26'."""
    if df.empty:
        return []
    return [p.strftime("%b %y") for p in pd.period_range(df["date"].min(), df["date"].max(), freq="M")]


def filter_rows(df: pd.DataFrame, categories: list[str] | None = None, months: list[str] | None = None,
                payee: str | None = None, search: str = "") -> pd.DataFrame:
    """Rows matching the chosen categories, months (labels from month_labels), payee and search text."""
    out = df
    if categories:
        out = out[out["category"].isin(categories)]
    if months:
        out = out[out["date"].dt.strftime("%b %y").isin(months)]
    if payee:
        out = out[out["payee"] == payee]
    if search.strip():
        out = out[out["payee"].str.contains(search.strip(), case=False, regex=False)]
    return out


def category_by_month(df: pd.DataFrame, month_order: list[str]) -> pd.DataFrame:
    """Spend per category for each month (rows = month labels, columns = categories in fixed order)."""
    rows = _spending(df)
    if rows.empty:
        return pd.DataFrame(index=month_order)
    rows["month"] = rows["date"].dt.strftime("%b %y")
    pivot = rows.pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0.0)
    pivot = pivot.reindex(month_order, fill_value=0.0).clip(lower=0)
    cols = [c for c in SPENDING_CATEGORIES if c in pivot.columns and pivot[c].sum() > 0]
    return pivot[cols]


def daily_spend(df: pd.DataFrame) -> pd.DataFrame:
    """Spend per day with the biggest payees that day: columns date, amount, payees."""
    rows = _spending(df)
    if rows.empty:
        return pd.DataFrame(columns=["date", "amount", "payees"])
    rows["day"] = rows["date"].dt.normalize()
    grouped = rows.groupby("day").agg(amount=("amount", "sum"))
    top = rows.sort_values("amount", ascending=False).groupby("day")["payee"].apply(
        lambda s: ", ".join(dict.fromkeys(p.title() for p in s.head(3))))
    out = grouped.join(top.rename("payees")).reset_index().rename(columns={"day": "date"})
    return out[out["amount"] > 0].reset_index(drop=True)


def weekday_average(daily: pd.DataFrame, all_days: pd.DatetimeIndex) -> pd.Series:
    """Average spend for each weekday (Mon=0) over every calendar day in the range, zero-spend days included."""
    full = daily.set_index("date")["amount"].reindex(all_days, fill_value=0.0)
    return full.groupby(full.index.dayofweek).mean().reindex(range(7), fill_value=0.0)


def payee_payments(df: pd.DataFrame, payee: str) -> pd.DataFrame:
    """Every payment to one payee, newest first: date, amount, category."""
    rows = df[(df["payee"] == payee) & (df["debit"] > 0)]
    return rows[["date", "debit", "category"]].rename(columns={"debit": "amount"}).sort_values("date", ascending=False).reset_index(drop=True)

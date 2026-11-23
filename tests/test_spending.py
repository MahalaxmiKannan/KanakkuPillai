from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from core.categorizer import SPENDING_CATEGORIES, TRANSFERS
from core.parsers import parse_statement
from core.spending import (
    apply_overrides,
    by_category,
    format_inr,
    monthly_trend,
    recurring_payments,
    same_payee_ids,
    summary,
    top_merchants,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def df():
    data = [
        ("2026-01-05", "swiggy", 300, 0, "Food & dining"),
        ("2026-01-09", "swiggy", 200, 0, "Food & dining"),
        ("2026-01-10", "amazon", 1000, 0, "Shopping"),
        ("2026-01-12", "amazon", 0, 400, "Shopping"),          # refund
        ("2026-01-15", "priya k", 700, 0, TRANSFERS),
        ("2026-01-16", "priya k", 0, 200, TRANSFERS),
        ("2026-01-01", "employer", 0, 20000, "Income"),
        ("2026-03-05", "jio", 299, 0, "Bills & recharge"),
    ]
    return pd.DataFrame(
        [{"date": pd.Timestamp(d), "payee": p, "debit": float(dr), "credit": float(cr), "category": c,
          "source": "rule", "needs_review": False} for d, p, dr, cr, c in data]
    )


@pytest.mark.parametrize("amount, text", [
    (0, "₹0"), (999, "₹999"), (1000, "₹1,000"), (105570, "₹1,05,570"),
    (12345678, "₹1,23,45,678"), (-2500, "-₹2,500"),
])
def test_format_inr_uses_indian_grouping(amount, text):
    assert format_inr(amount) == text


def test_by_category_nets_refunds_and_excludes_income_and_transfers(df):
    totals = by_category(df)
    assert totals["Food & dining"] == 500
    assert totals["Shopping"] == 600
    assert TRANSFERS not in totals.index and "Income" not in totals.index


def test_by_category_keeps_a_fixed_order(df):
    order = [SPENDING_CATEGORIES.index(c) for c in by_category(df).index]
    assert order == sorted(order)


def test_monthly_trend_includes_months_with_no_spending(df):
    trend = monthly_trend(df)
    assert trend.tolist() == [1100, 0, 299]


def test_top_merchants_are_ranked_by_net_spend(df):
    assert top_merchants(df)["payee"].tolist() == ["amazon", "swiggy", "jio"]
    assert len(top_merchants(df, n=1)) == 1


def test_summary_numbers(df):
    s = summary(df)
    assert s["total"] == 1399
    assert s["months"] == 3
    assert s["avoidable"] == 1100
    assert s["transfers_out"] == 700


def test_summary_of_empty_spending_does_not_crash(df):
    assert summary(df[df["category"] == "Income"])["avoidable_share"] == 0


def test_overrides_move_money_between_categories(df):
    edited = apply_overrides(df, {4: "Education"})
    assert by_category(edited)["Education"] == 700
    assert edited.loc[4, "source"] == "you"
    assert df.loc[4, "category"] == TRANSFERS            # original is untouched


def test_same_payee_keeps_money_out_and_in_separate(df):
    assert same_payee_ids(df, 0) == [0, 1]
    assert same_payee_ids(df, 4) == [4]


def test_recurring_finds_steady_monthly_payments_only():
    rows = []
    for month in range(1, 5):
        rows.append((f"2026-0{month}-11", "netflix", 149))
        rows.append((f"2026-0{month}-12", "swiggy", 100 * month))
        rows.append((f"2026-0{month}-13", "zomato", 200))
        rows.append((f"2026-0{month}-20", "zomato", 200))
    df = pd.DataFrame(
        [{"date": pd.Timestamp(d), "payee": p, "debit": float(a), "credit": 0.0, "category": "Subscriptions"}
         for d, p, a in rows]
    )
    found = recurring_payments(df)
    assert found["payee"].tolist() == ["netflix"]
    assert found["yearly"].iloc[0] == 149 * 12


def test_recurring_needs_three_months(df):
    assert recurring_payments(df).empty


def run_page(**state):
    page = AppTest.from_file(str(ROOT / "pages" / "2_My_Spending.py"), default_timeout=60)
    for key, value in state.items():
        page.session_state[key] = value
    return page.run()


def metric(page, label):
    return next(m.value for m in page.metric if m.label == label)


def test_page_without_data_offers_the_demo():
    page = run_page()
    assert not page.exception
    assert any(b.label == "Try the demo" for b in page.button)


def test_page_shows_demo_dashboard():
    demo = parse_statement(ROOT / "data" / "demo_statement.csv", "standard")
    page = run_page(transactions=demo)
    assert not page.exception
    assert metric(page, "Total spent").startswith("₹")


def test_page_totals_follow_a_correction():
    demo = parse_statement(ROOT / "data" / "demo_statement.csv", "standard")
    page = run_page(transactions=demo)
    before = page.session_state["categorized"]
    swiggy = before.index[before["payee"] == "swiggy"].tolist()
    amount = before.loc[swiggy, "debit"].sum()
    expected = summary(before)["total"] - amount

    page.session_state["category_overrides"] = {i: TRANSFERS for i in swiggy}
    page.run()
    assert not page.exception
    assert metric(page, "Total spent") == format_inr(expected)


def test_filter_rows_and_month_labels(df):
    from core.spending import filter_rows, month_labels
    assert month_labels(df)[0] == "Jan 26"
    only_food = filter_rows(df, categories=["Food & dining"])
    assert set(only_food["category"]) == {"Food & dining"}
    assert filter_rows(df, months=["Jan 26"]).shape[0] == df.shape[0] - 1      # the March payment drops out
    assert filter_rows(df, months=["Dec 25"]).empty
    assert set(filter_rows(df, payee="amazon")["payee"]) == {"amazon"}
    assert not filter_rows(df, search="SWIG").empty


def test_category_by_month_and_daily(df):
    from core.spending import category_by_month, daily_spend, month_labels, payee_payments, weekday_average
    months = month_labels(df)
    m = category_by_month(df, months)
    assert list(m.index) == months
    assert m.loc["Jan 26", "Food & dining"] == 500          # 300 + 200
    assert m.loc["Jan 26", "Shopping"] == 600                # 1000 - 400 refund
    d = daily_spend(df)
    assert d["amount"].sum() == 1799        # a refund on another day is not netted off a day with no spending
    days = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    assert weekday_average(d, days).shape == (7,)
    assert len(payee_payments(df, "swiggy")) == 2


def test_spending_page_filters_change_the_numbers():
    page = str(ROOT / "pages" / "2_My_Spending.py")
    at = AppTest.from_file(page, default_timeout=90)
    at.session_state["transactions"] = parse_statement(ROOT / "data" / "demo_statement.csv", "standard")
    at.run()
    assert not at.exception
    everything = [m.value for m in at.metric]
    at.session_state["f_cats"] = ["Food & dining"]
    at.session_state["f_months"] = ["Jul 26"]
    at.run()
    assert not at.exception
    filtered = [m.value for m in at.metric]
    assert filtered[0] != everything[0]            # total spent changes with the filters
    assert filtered[0] == filtered[2]              # only an avoidable category is selected


def test_spending_page_checker_is_hidden_until_asked_and_next_button_exists():
    page = str(ROOT / "pages" / "2_My_Spending.py")
    at = AppTest.from_file(page, default_timeout=90)
    at.session_state["transactions"] = parse_statement(ROOT / "data" / "demo_statement.csv", "standard")
    at.run()
    assert not at.exception
    assert len(at.multiselect) == 2                                   # categories and months are dropdown filters
    assert not at.dataframe or all("Category" not in list(d.value.columns) or len(d.value) < 50 for d in at.dataframe)
    assert not any("Spotted a wrong category" in m.value for m in at.markdown)      # the checker starts closed
    assert any(b.label == "Next: My Surplus →" for b in at.button)
    check = next(b for b in at.button if b.label.startswith("Check your categories"))
    check.click().run()
    assert not at.exception
    assert any("Spotted a wrong category" in m.value for m in at.markdown)          # opens only after the click

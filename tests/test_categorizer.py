import pandas as pd
import pytest

from core.categorizer import CATEGORIES, INCOME, TRANSFERS, categorize, load_model, looks_like_person, match_merchant
from core.merchants import MERCHANTS
from core.parsers import parse_statement


def rows(*items):
    """Build transactions from (date, payee, debit, credit, description)."""
    return pd.DataFrame(
        [
            {"date": pd.Timestamp(d), "payee": p, "debit": float(dr), "credit": float(cr), "description": text}
            for d, p, dr, cr, text in items
        ]
    )


def test_dictionary_has_about_150_merchants():
    assert sum(len(keys) for keys in MERCHANTS.values()) >= 150


@pytest.mark.parametrize("payee, category", [
    ("swiggy", "Food & dining"),
    ("swiggy instamart", "Groceries"),          # longest key wins
    ("amazon prime", "Subscriptions"),
    ("amazon", "Shopping"),
    ("SWIGGYLIMITED", "Food & dining"),         # joined-up names
    ("big basket", "Groceries"),
    ("jio prepaid", "Bills & recharge"),
    ("ola", "Travel"),
    ("sri ram medicals", "Health"),
])
def test_merchant_rules(payee, category):
    assert match_merchant(payee) == category


@pytest.mark.parametrize("payee", ["kolar stores", "priya k", "unknown", "", None])
def test_short_keys_do_not_match_inside_words(payee):
    assert match_merchant(payee) is None


@pytest.mark.parametrize("payee, expected", [
    ("priya k", True), ("arjun kumar", True), ("kumar stores", False),
    ("acme pvt ltd", False), ("unknown", False), ("shop 24", False),
])
def test_looks_like_person(payee, expected):
    assert looks_like_person(payee) is expected


def test_salary_and_stipend_are_income():
    out = categorize(rows(("2026-01-05", "brightpath labs", 0, 10000, "NEFT/CR/BRIGHTPATH LABS/STIPEND")), model=None)
    assert out["category"].iloc[0] == INCOME


def test_regular_monthly_sender_is_income_but_a_friend_is_not():
    out = categorize(rows(
        ("2026-01-01", "suresh kumar", 0, 7000, "x"),
        ("2026-02-01", "suresh kumar", 0, 7000, "x"),
        ("2026-03-01", "suresh kumar", 0, 7000, "x"),
        ("2026-03-09", "divya m", 0, 300, "x"),
    ), model=None)
    assert out["category"].tolist() == [INCOME, INCOME, INCOME, TRANSFERS]


def test_merchant_refund_keeps_merchant_category():
    out = categorize(rows(("2026-01-05", "amazon", 0, 499, "refund")), model=None)
    assert out["category"].iloc[0] == "Shopping"


def test_atm_cash_is_a_transfer():
    out = categorize(rows(("2026-01-05", "atm wdl", 1000, 0, "ATM WDL/SBI ATM")), model=None)
    assert out["category"].iloc[0] == TRANSFERS


def test_without_a_model_unknown_business_is_flagged_for_review():
    out = categorize(rows(("2026-01-05", "acme pvt ltd", 500, 0, "x")), model=None)
    assert out["needs_review"].iloc[0]


def test_saved_model_loads_and_knows_the_spending_categories():
    model = load_model()
    assert model is not None
    assert set(model.classes_) <= set(CATEGORIES) and INCOME not in model.classes_


def test_demo_statement_is_categorized_correctly():
    from pathlib import Path

    demo = Path(__file__).resolve().parents[1] / "data" / "demo_statement.csv"
    out = categorize(parse_statement(demo, "standard"))
    by_payee = out.drop_duplicates("payee").set_index("payee")["category"]
    assert by_payee["swiggy"] == "Food & dining"
    assert by_payee["blinkit"] == "Groceries"
    assert by_payee["netflix"] == "Subscriptions"
    assert by_payee["hostel mess fee"] == "Education"
    assert by_payee["suresh kumar"] == INCOME
    assert out["category"].isin(CATEGORIES).all()

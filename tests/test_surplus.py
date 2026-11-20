import pandas as pd
import pytest

from core.categorizer import TRANSFERS
from core.risk_quiz import QUESTIONS, profile_for, result, score
from core.surplus import compute_surplus


@pytest.fixture
def df():
    rows = [
        ("2026-01-01", "employer", 0, 30000, "Income"),
        ("2026-02-01", "employer", 0, 30000, "Income"),
        ("2026-01-05", "landlord", 8000, 0, "Rent"),
        ("2026-02-05", "landlord", 8000, 0, "Rent"),
        ("2026-01-10", "swiggy", 2000, 0, "Food & dining"),
        ("2026-02-10", "swiggy", 2000, 0, "Food & dining"),
        ("2026-01-15", "friend", 3000, 0, TRANSFERS),
    ]
    return pd.DataFrame([{"date": pd.Timestamp(d), "payee": p, "debit": float(dr), "credit": float(cr), "category": c}
                         for d, p, dr, cr, c in rows])


def test_basic_numbers(df):
    r = compute_surplus(df)
    assert r["income"] == 30000
    assert r["essentials"] == 8000          # rent counts as essential
    assert r["discretionary"] == 2000
    assert r["surplus"] == 20000
    assert r["emergency_target"] == 24000   # 3 x essentials


def test_emergency_fund_comes_first(df):
    r = compute_surplus(df, emergency_saved=0)
    assert r["to_emergency_fund"] == 20000
    assert r["left_after_fund"] == 0
    assert r["months_to_fund"] == pytest.approx(1.2)
    full = compute_surplus(df, emergency_saved=24000)
    assert full["emergency_progress"] == 1.0
    assert full["left_after_fund"] == 20000


def test_transfers_only_counted_when_asked(df):
    assert compute_surplus(df)["spend"] == 10000
    r = compute_surplus(df, count_transfers=True)
    assert r["transfers_counted"] == 1500    # 3000 over 2 months
    assert r["surplus"] == 18500


def test_income_override_and_no_surplus(df):
    r = compute_surplus(df, income_override=5000)
    assert r["surplus"] < 0 and r["safe_to_set_aside"] == 0


def test_no_income_found(df):
    r = compute_surplus(df[df["category"] != "Income"])
    assert r["income"] == 0 and r["safe_to_set_aside"] == 0


def test_quiz_bands_and_validation():
    n = len(QUESTIONS)
    assert score([0] * n) == n and profile_for(n) == "Conservative"
    assert profile_for(16) == "Moderate" and profile_for(21) == "Moderate"
    assert profile_for(3 * n) == "Aggressive"
    with pytest.raises(ValueError):
        score([0] * (n - 1))
    with pytest.raises(ValueError):
        score([3] * n)


def test_quiz_warns_when_no_emergency_cover():
    answers = [2] * len(QUESTIONS)
    answers[3] = 0
    assert result(answers)["notes"]


def test_pages_render():
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from core.parsers import parse_statement

    root = Path(__file__).resolve().parents[1]
    demo = parse_statement(root / "data" / "demo_statement.csv", "standard")
    for page in ["3_My_Surplus.py", "4_Risk_Quiz.py", "5_Learn.py"]:
        at = AppTest.from_file(str(root / "app.py"), default_timeout=30)
        at.session_state["transactions"] = demo
        at.run()
        at.switch_page(f"pages/{page}").run()
        assert not at.exception, (page, at.exception)
    at = AppTest.from_file(str(root / "app.py"), default_timeout=30)
    at.run()
    at.switch_page("pages/3_My_Surplus.py").run()   # no statement loaded: friendly message, no crash
    assert not at.exception

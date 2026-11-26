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
    for page in ["5_My_Surplus.py", "3_Risk_Quiz.py", "4_Learn.py"]:
        at = AppTest.from_file(str(root / "app.py"), default_timeout=30)
        at.session_state["transactions"] = demo
        at.run()
        at.switch_page(f"pages/{page}").run()
        assert not at.exception, (page, at.exception)
    at = AppTest.from_file(str(root / "app.py"), default_timeout=30)
    at.run()
    at.switch_page("pages/5_My_Surplus.py").run()   # no statement loaded: friendly message, no crash
    assert not at.exception


def test_flipbook_builds_every_chapter():
    from pathlib import Path
    from core.flipbook import build_book, load_chapters, md_to_html

    chapters = load_chapters(Path(__file__).resolve().parents[1] / "content")
    assert len(chapters) == 7 and all(c["teaser"] for c in chapters)
    book = build_book(chapters)
    assert book.count('class="leaf"') == 8          # cover + one leaf per chapter
    assert "<script>alert" not in md_to_html("<script>alert(1)</script>")   # escaped


def test_runway_helpers():
    from core.surplus import avoidable_per_month, describe_duration, months_to_full, runway
    assert months_to_full(1000, 0, 10000) == 10
    assert months_to_full(0, 0, 10000) is None
    assert months_to_full(500, 20000, 10000) == 0.0
    assert runway(4000, 0, 10000, 4) == [0, 4000, 8000, 10000, 10000]      # capped at the target
    assert describe_duration(None) == "not reachable at this pace"
    assert describe_duration(0.4) == "under a month"
    assert describe_duration(10.2) == "11 months"
    assert describe_duration(103) == "8.6 years"
    rows = pd.DataFrame([
        {"date": pd.Timestamp("2026-01-10"), "payee": "swiggy", "debit": 600.0, "credit": 0.0, "category": "Food & dining"},
        {"date": pd.Timestamp("2026-02-10"), "payee": "swiggy", "debit": 400.0, "credit": 0.0, "category": "Food & dining"},
        {"date": pd.Timestamp("2026-02-11"), "payee": "dmart", "debit": 900.0, "credit": 0.0, "category": "Groceries"},
    ])
    assert avoidable_per_month(rows) == 500.0                               # 1000 over 2 months, groceries excluded


def test_surplus_page_renders_and_lever_changes_the_plan():
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from core.parsers import parse_statement
    root = Path(__file__).resolve().parents[1]
    at = AppTest.from_file(str(root / "pages" / "5_My_Surplus.py"), default_timeout=90)
    at.session_state["transactions"] = parse_statement(root / "data" / "demo_statement.csv", "standard")
    at.run()
    assert not at.exception
    base = at.session_state["surplus"]["safe_to_set_aside"]
    assert base > 0
    at.slider[0].set_value(60).run()
    assert not at.exception
    assert at.session_state["surplus"]["safe_to_set_aside"] == base            # the page keeps the real figure; only the lever is a what-if
    assert any("With the trim" in m.value for m in at.markdown)


def test_journey_order_is_consistent():
    """The nav, the step tracker and the page files all follow Upload > Spending > Quiz > Learn > Surplus > Simulator > Scam."""
    import re
    from core.ui import STEPS
    order = ["Upload", "Spending", "Risk quiz", "Learn", "Surplus", "Simulator", "Scam check"]
    assert [name for name, _ in STEPS] == order
    nav = (root_dir() / "app.py").read_text(encoding="utf-8")
    assert [p for p, _ in re.findall(r'pages/(\d)_(\w+)\.py', nav)] == ["1", "2", "3", "4", "5", "6", "7", "8"]
    for number, (_, path) in enumerate(STEPS, start=1):
        assert path.startswith(f"pages/{number}_") and (root_dir() / path).exists()


def root_dir():
    from pathlib import Path
    return Path(__file__).resolve().parents[1]


def test_quiz_page_one_question_at_a_time():
    from streamlit.testing.v1 import AppTest
    from core.risk_quiz import QUESTIONS
    at = AppTest.from_file(str(root_dir() / "pages" / "3_Risk_Quiz.py"), default_timeout=60).run()
    assert not at.exception
    assert len(at.radio) == 1                                        # one question on the card at a time
    nxt = lambda: next(b for b in at.button if b.label == "Next →")  # noqa: E731
    assert nxt().disabled                                            # can't move on without an answer
    at.radio[0].set_value(QUESTIONS[0]["options"][1]).run()
    nxt().click().run()
    assert "Question 2 of 9" in at.markdown[-1].value or any("Question 2 of 9" in m.value for m in at.markdown)
    next(b for b in at.button if b.label == "← Back").click().run()   # back: the first answer is still there
    assert at.radio[0].value == QUESTIONS[0]["options"][1]
    nxt().click().run()
    for q in QUESTIONS[1:]:
        at.radio[0].set_value(q["options"][1]).run()
        label = "Finish quiz ✓" if q is QUESTIONS[-1] else "Next →"
        next(b for b in at.button if b.label == label).click().run()
    assert not at.exception
    res = at.session_state["risk_result"]
    assert res["total"] == 18 and res["profile"] == "Moderate"
    assert any("Moderate" in m.value for m in at.markdown)
    assert any(b.label == "Start learning →" for b in at.button)
    next(b for b in at.button if b.label == "Retake the quiz").click().run()
    assert "risk_result" not in at.session_state and len(at.radio) == 1

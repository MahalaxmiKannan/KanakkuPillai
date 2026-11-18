"""Parsed totals must match the statement's own totals, to the paisa."""
from pathlib import Path

import pandas as pd
import pytest

from core.parsers import STANDARD_COLUMNS, StatementParseError, find_balance_gaps, parse_statement, summarize

DATA = Path(__file__).resolve().parents[1] / "data"


def test_sbi_sample_matches_statement_totals():
    df = parse_statement(DATA / "samples" / "sbi_sample.csv", "sbi")
    s = summarize(df)
    assert s["rows"] == 7
    assert s["total_debit"] == 342 + 299 + 1000 + 250 + 149
    assert s["total_credit"] == 7000 + 23
    # opening 5,000 + credits - debits == closing balance printed by the bank
    assert 5000 + s["total_credit"] - s["total_debit"] == df["balance"].iloc[-1] == 9983.00


def test_hdfc_sample_matches_statement_summary():
    df = parse_statement(DATA / "samples" / "hdfc_sample.csv", "hdfc")
    s = summarize(df)
    # Numbers from the bank's own STATEMENT SUMMARY block at the bottom
    assert s["rows"] == 4 + 2
    assert s["total_debit"] == 2412.50
    assert s["total_credit"] == 10320.00
    assert df["balance"].iloc[-1] == 12158.00


def test_hdfc_dates_are_day_first():
    df = parse_statement(DATA / "samples" / "hdfc_sample.csv", "hdfc")
    assert df["date"].iloc[1] == pd.Timestamp("2026-10-04")   # 04/10/26 is 4 Oct, not 10 Apr


def test_demo_statement_balance_is_consistent():
    df = parse_statement(DATA / "demo_statement.csv", "standard")
    assert len(df) > 200
    assert df["date"].min() >= pd.Timestamp("2026-05-01")
    opening = df["balance"].iloc[0] + df["debit"].iloc[0] - df["credit"].iloc[0]
    closing = opening + df["credit"].sum() - df["debit"].sum()
    assert closing == pytest.approx(df["balance"].iloc[-1])


def test_output_has_standard_columns_and_types():
    df = parse_statement(DATA / "samples" / "sbi_sample.csv", "sbi")
    assert list(df.columns) == STANDARD_COLUMNS
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert (df["debit"] >= 0).all() and (df["credit"] >= 0).all()
    assert df["date"].is_monotonic_increasing


def test_parsed_output_is_masked():
    for name, bank in [("sbi_sample.csv", "sbi"), ("hdfc_sample.csv", "hdfc")]:
        text = " ".join(parse_statement(DATA / "samples" / name, bank)["description"])
        assert "suresh.kumar64@" not in text and "priyak2005@" not in text
        assert "9876501234" not in text and "4123XXXXXXXX5678" not in text


def test_payees_are_extracted():
    sbi = parse_statement(DATA / "samples" / "sbi_sample.csv", "sbi")["payee"].tolist()
    hdfc = parse_statement(DATA / "samples" / "hdfc_sample.csv", "hdfc")["payee"].tolist()
    assert "swiggy" in sbi and "jio prepaid" in sbi and "priya k" in sbi
    assert "zomato ltd" in hdfc and "uber india" in hdfc and "blinkit" in hdfc


def test_sbi_simple_export_with_date_and_details_headers():
    """SBI also exports a plain table: Date, Details, Debit, Credit, Balance."""
    csv = (
        b"Date,Details,Debit,Credit,Balance\n"
        b'10-10-2026,"WDL TFR\nUPI/DR/412345678901/SWIGGY/YESB/swiggy/ UPI 1234567890123 AT 01234 MAIN ROAD",250.5,,1000\n'
        b"11-10-2026,DEP TFR UPI/CR/412345678902/RAVI K/SBIN/ravikumar/ UPI 1234567890123 AT 01234 MAIN ROAD,,500,1500\n"
    )
    df = parse_statement(csv, "sbi")
    assert df["date"].tolist() == [pd.Timestamp("2026-10-10"), pd.Timestamp("2026-10-11")]
    assert df["payee"].tolist() == ["swiggy", "ravi k"]
    assert df["debit"].sum() == 250.5 and df["credit"].sum() == 500
    assert "ravikumar" not in " ".join(df["description"])


def test_wrong_bank_gives_friendly_error():
    with pytest.raises(StatementParseError, match="column headers"):
        parse_statement(DATA / "samples" / "sbi_sample.csv", "hdfc")


def test_empty_file_gives_friendly_error():
    with pytest.raises(StatementParseError, match="empty"):
        parse_statement(b"", "standard")


def test_headers_but_no_rows():
    with pytest.raises(StatementParseError):
        parse_statement(b"date,description,debit,credit,balance\n", "standard")


def test_unknown_bank():
    with pytest.raises(StatementParseError, match="Unknown bank"):
        parse_statement(b"x", "kotak")

def test_no_balance_gaps_in_clean_statement():
    df = parse_statement(DATA / "samples" / "sbi_sample.csv", "sbi")
    assert find_balance_gaps(df).empty


def test_missing_transaction_is_detected():
    df = parse_statement(DATA / "samples" / "sbi_sample.csv", "sbi")
    df = df.drop(index=2).reset_index(drop=True)     # pretend one row is missing
    gaps = find_balance_gaps(df)
    assert len(gaps) == 1
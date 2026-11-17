"""Read bank statement CSVs into one standard DataFrame.

Every supported bank gets a small BankConfig that says which of its
columns map to our standard ones. Banks put account details above the
table and summaries below it, so we search for the header row instead
of assuming it is row 1, and drop any row whose date doesn't parse.

Standard output columns (one row per transaction, oldest first):
    date (datetime) | description (masked) | payee | debit | credit | balance
"""
from __future__ import annotations

import csv
import io
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from core.masking import mask_transactions
from core.payee import clean_payee

STANDARD_COLUMNS = ["date", "description", "payee", "debit", "credit", "balance"]


class StatementParseError(ValueError):
    """Raised with a message that is safe to show to the user."""


@dataclass(frozen=True)
class BankConfig:
    name: str
    # standard column -> list of header names this bank might use
    columns: dict[str, list[str]]
    date_formats: list[str] = field(default_factory=list)
    note: str = ""


# Layouts based on the common net-banking CSV exports.
# CHECK THESE against your own statements and adjust the header names.
BANKS: dict[str, BankConfig] = {
    "sbi": BankConfig(
        name="SBI",
        columns={
            "date": ["Txn Date", "Transaction Date"],
            "description": ["Description", "Narration"],
            "debit": ["Debit", "Withdrawal"],
            "credit": ["Credit", "Deposit"],
            "balance": ["Balance"],
        },
        date_formats=["%d %b %Y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y"],
        note="SBI net banking > Account Statement > download as CSV/Excel (saved as CSV).",
    ),
    "hdfc": BankConfig(
        name="HDFC Bank",
        columns={
            "date": ["Date"],
            "description": ["Narration"],
            "debit": ["Withdrawal Amt.", "Withdrawal Amount", "Debit Amount"],
            "credit": ["Deposit Amt.", "Deposit Amount", "Credit Amount"],
            "balance": ["Closing Balance"],
        },
        date_formats=["%d/%m/%y", "%d/%m/%Y"],
        note="HDFC net banking > Accounts > Download statement > Delimited (CSV).",
    ),
    "standard": BankConfig(
        name="Standard CSV (any bank)",
        columns={
            "date": ["date"],
            "description": ["description"],
            "debit": ["debit"],
            "credit": ["credit"],
            "balance": ["balance"],
        },
        date_formats=["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"],
        note="Columns: date, description, debit, credit, balance. The demo uses this.",
    ),
}

REQUIRED = ["date", "description", "debit", "credit"]   # balance is optional


def _norm(text: str) -> str:
    """'Withdrawal Amt.' -> 'withdrawalamt' so small header differences don't matter."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def _read_rows(source: str | Path | bytes | BinaryIO) -> list[list[str]]:
    """Read raw CSV rows from a path, bytes, or an uploaded file object."""
    if isinstance(source, (str, Path)):
        raw = Path(source).read_bytes()
    elif isinstance(source, bytes):
        raw = source
    else:
        raw = source.read()
        if hasattr(source, "seek"):
            source.seek(0)
    if not raw:
        raise StatementParseError("The file is empty.")
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    return [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(text), delimiter=delimiter)]


def _find_header(rows: list[list[str]], config: BankConfig) -> tuple[int, dict[str, int]]:
    """Return (header row index, {standard column: position})."""
    wanted = {std: {_norm(h) for h in names} for std, names in config.columns.items()}
    for i, row in enumerate(rows[:60]):            # header is always near the top
        cells = [_norm(c) for c in row]
        positions = {}
        for std, names in wanted.items():
            for j, cell in enumerate(cells):
                if cell in names:
                    positions[std] = j
                    break
        if all(col in positions for col in REQUIRED):
            return i, positions
    expected = ", ".join(config.columns[c][0] for c in REQUIRED)
    raise StatementParseError(
        f"Couldn't find the {config.name} column headers ({expected}). "
        "Is this the right bank, and is it the CSV export?"
    )


def _parse_amount(values: pd.Series) -> pd.Series:
    """'1,234.50', '₹ 500', '200.00 Cr', '' -> floats (blank -> 0)."""
    cleaned = (
        values.astype(str)
        .str.replace(r"(?i)\b(cr|dr|inr|rs)\b\.?|₹|,|\s", "", regex=True)
        .replace({"": None, "-": None, "nan": None, "None": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _parse_dates(values: pd.Series, formats: list[str]) -> pd.Series:
    """Try each known format; Indian statements are day-first, never month-first."""
    result = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    for fmt in formats:
        missing = result.isna()
        if not missing.any():
            break
        result[missing] = pd.to_datetime(values[missing], format=fmt, errors="coerce")
    missing = result.isna()
    if missing.any():
        # Leftovers are usually footer text ("STATEMENT SUMMARY"); they become NaT.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            result[missing] = pd.to_datetime(values[missing], dayfirst=True, errors="coerce")
    return result


def parse_statement(source, bank: str) -> pd.DataFrame:
    """Parse a statement CSV into the standard, masked format."""
    if bank not in BANKS:
        raise StatementParseError(f"Unknown bank '{bank}'. Choose one of: {', '.join(BANKS)}")
    config = BANKS[bank]

    rows = _read_rows(source)
    header_idx, positions = _find_header(rows, config)

    body = rows[header_idx + 1:]
    width = max(positions.values()) + 1
    body = [row + [""] * (width - len(row)) for row in body if any(row)]
    if not body:
        raise StatementParseError("Found the headers but no transactions under them.")

    table = pd.DataFrame({std: [row[j] for row in body] for std, j in positions.items()})

    df = pd.DataFrame({
        "date": _parse_dates(table["date"], config.date_formats),
        "description": table["description"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip(),
        "debit": _parse_amount(table["debit"]),
        "credit": _parse_amount(table["credit"]),
        "balance": _parse_amount(table["balance"]) if "balance" in table else float("nan"),
    })

    # Rows without a real date are separators, totals or footer text.
    df = df[df["date"].notna()]
    df[["debit", "credit"]] = df[["debit", "credit"]].fillna(0.0)
    df = df[(df["debit"] > 0) | (df["credit"] > 0)]
    if df.empty:
        raise StatementParseError("No transactions found. The file may be in a different format.")

    # Payee comes from the raw text; masking then hides IDs in the description.
    df["payee"] = df["description"].map(clean_payee)
    df = mask_transactions(df, "description")

    df = df.sort_values("date", kind="stable").reset_index(drop=True)
    return df[STANDARD_COLUMNS]


def summarize(df: pd.DataFrame) -> dict:
    """Totals used by tests and the Upload page."""
    return {
        "rows": len(df),
        "total_debit": round(float(df["debit"].sum()), 2),
        "total_credit": round(float(df["credit"].sum()), 2),
        "start": df["date"].min(),
        "end": df["date"].max(),
    }

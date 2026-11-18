"""Find rows the parser skipped and places where the balance doesn't add up.

Runs on your laptop only. Prints dates, amounts and the KIND of problem,
never full descriptions, so the output is safe to share.

    python -m scripts.check_statement data/raw/sbi_statement.csv sbi
"""
import sys

import pandas as pd

from core.parsers import BANKS, _find_header, _parse_amount, _parse_dates, _read_rows


def main(path: str, bank: str) -> None:
    config = BANKS[bank]
    rows = _read_rows(path)
    header_idx, pos = _find_header(rows, config)
    width = max(pos.values()) + 1

    print(f"Header found on line {header_idx + 1} of the file.\n")
    print("--- 1. Rows the parser SKIPPED (that had something in them) ---")
    skipped = 0
    for line_no, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        if not any(row):
            continue
        row = row + [""] * (width - len(row))
        cells = {std: row[j] for std, j in pos.items()}
        date = _parse_dates(pd.Series([cells["date"]]), config.date_formats).iloc[0]
        debit = _parse_amount(pd.Series([cells["debit"]])).fillna(0).iloc[0]
        credit = _parse_amount(pd.Series([cells["credit"]])).fillna(0).iloc[0]
        if pd.notna(date) and (debit > 0 or credit > 0):
            continue  # this row was kept
        skipped += 1
        reason = "date didn't parse" if pd.isna(date) else "debit/credit didn't parse or are 0"
        print(f"line {line_no}: {reason}")
        print(f"    date cell   = {cells['date']!r}")
        print(f"    debit cell  = {cells['debit']!r}")
        print(f"    credit cell = {cells['credit']!r}")
        print(f"    description = {len(cells['description'])} characters (hidden)")
    if not skipped:
        print("none")

    print("\n--- 2. Balance jumps (balance changed by more than the row's amount) ---")
    from core.parsers import parse_statement
    df = parse_statement(path, bank)
    expected = df["balance"].shift(1) + df["credit"] - df["debit"]
    gaps = df[(df["balance"] - expected).abs() > 0.01].iloc[0:]
    gaps = gaps[gaps.index > 0]
    for i, r in gaps.iterrows():
        prev = df.loc[i - 1]
        print(f"between {prev['date']:%d-%m-%Y} and {r['date']:%d-%m-%Y} (parsed row {i}): "
              f"off by {r['balance'] - expected[i]:+.2f}")
    if gaps.empty:
        print("none - every row's balance adds up")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
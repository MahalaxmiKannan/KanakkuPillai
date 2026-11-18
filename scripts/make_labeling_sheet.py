"""Build data/raw/to_label.csv from your real statements, ready for hand-labelling.

Reads every statement in data/raw/, pre-fills the app's best guess, and puts the
least certain rows first. Git ignores data/raw/, so this stays on your computer.

    python scripts/make_labeling_sheet.py

Then fill in the `label` column in Excel and save the file as data/raw/labeled_real.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.categorizer import CATEGORIES, categorize  # noqa: E402
from core.parsers import BANKS, StatementParseError, parse_statement  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = RAW / "to_label.csv"
SKIP = {"to_label.csv", "labeled_real.csv"}


def read_any_bank(path: Path) -> pd.DataFrame | None:
    for bank in BANKS:
        try:
            return parse_statement(path, bank)
        except StatementParseError:
            continue
    return None


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT.name} already exists. Use --force to replace it (your labels would be lost).")

    frames = []
    for path in sorted(RAW.glob("*.csv")):
        if path.name in SKIP:
            continue
        df = read_any_bank(path)
        print(f"{path.name}: {'could not be read' if df is None else f'{len(df)} transactions'}")
        if df is not None:
            frames.append(df)
    if not frames:
        raise SystemExit("No readable statements found in data/raw/.")

    rows = categorize(pd.concat(frames, ignore_index=True))
    sheet = pd.DataFrame({
        "date": rows["date"].dt.strftime("%Y-%m-%d"),
        "payee": rows["payee"],
        "debit": rows["debit"],
        "credit": rows["credit"],
        "suggested": rows["category"],
        "decided_by": rows["source"],
        "confidence": rows["confidence"],
        "label": "",
    }).sort_values(["confidence", "payee"])
    sheet.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"\nWrote {len(sheet)} rows to {OUT}")
    print("Allowed labels:", " | ".join(CATEGORIES))


if __name__ == "__main__":
    main()

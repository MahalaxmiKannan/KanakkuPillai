"""Make the scam-message dataset safe to publish: data/raw/scam_messages.csv -> data/scam_messages.csv.

- masks names of real people, a place that shows where someone was, and a phone number
  (listed in the gitignored data/raw/private_terms.txt, so they never appear in the repo)
- defangs links in scam messages (https -> hxxps, dots -> [.]) so they can never be clicked
- masks the last digits of account numbers
- drops rows that are not about money

Run from the repo root:  python scripts/clean_scam_messages.py
The raw file stays in data/raw/ (gitignored); only the cleaned file is committed.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.scam_detector import defang  # noqa: E402

RAW = ROOT / "data" / "raw" / "scam_messages.csv"
OUT = ROOT / "data" / "scam_messages.csv"

# Real people's names (scammers borrow real analysts' names), a location and a personal number to mask.
# They live in a gitignored file, one per line, so the public repo never contains them.
PRIVATE_TERMS = ROOT / "data" / "raw" / "private_terms.txt"


def private_terms() -> list[str]:
    if not PRIVATE_TERMS.exists():
        return []
    lines = PRIVATE_TERMS.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


MASK_LITERALS = private_terms()
# Rows that are not financial messages at all.
DROP_IF_CONTAINS = ["Raya D1"]


def clean_text(text: str, is_scam: bool) -> str:
    for literal in MASK_LITERALS:
        text = text.replace(literal, "XXXX")
    text = re.sub(r"X{3,}\d+", "XXXX", text)           # XXXXXXXX146 -> XXXX (no partial account numbers)
    return defang(text) if is_scam else text


def main() -> None:
    if not MASK_LITERALS:
        sys.exit(f"Missing {PRIVATE_TERMS.relative_to(ROOT)}: list the names, places and numbers to mask, one per line.")
    df = pd.read_csv(RAW)
    before = len(df)
    df = df[~df["text"].apply(lambda t: any(d in t for d in DROP_IF_CONTAINS))].copy()
    df["text"] = [clean_text(t, bool(lab)) for t, lab in zip(df["text"], df["label"])]
    leftovers = [lit for lit in MASK_LITERALS + DROP_IF_CONTAINS if df["text"].str.contains(re.escape(lit)).any()]
    assert not leftovers, f"still present: {leftovers}"
    assert not df["text"].str.contains(r"https?://\S*wixsite", regex=True).any()
    df.to_csv(OUT, index=False)
    real = df[df["source"] == "real"]
    print(f"{before} -> {len(df)} rows; real held-out: {len(real)} ({int(real['label'].sum())} scam, "
          f"{int((real['label'] == 0).sum())} legitimate) -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

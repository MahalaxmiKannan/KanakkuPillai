"""Give every transaction a category: rules first, ML for whatever rules miss.

Order of decisions:
  1. Money in: salary-like words or a regular monthly sender -> Income.
  2. ATM cash -> Transfers (we can't see what the cash was spent on).
  3. Known merchant or shop-type keyword -> that merchant's category.
  4. Money out to anyone else -> ML model on the payee name.
  5. Low model confidence -> flagged so the user can check it.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from core.merchants import MERCHANTS

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "categorizer.joblib"

SPENDING_CATEGORIES = [
    "Food & dining", "Groceries", "Travel", "Shopping",
    "Bills & recharge", "Subscriptions", "Education", "Health",
]
TRANSFERS = "Transfers (P2P)"
INCOME = "Income"
CATEGORIES = SPENDING_CATEGORIES + [TRANSFERS, INCOME]

# Below this, the model's guess is shown as "please check".
MIN_CONFIDENCE = 0.55

INCOME_WORDS = re.compile(
    r"\b(salary|sal|stipend|payroll|wages|bonus|scholarship|interest|dividend|cemtex)\b", re.I
)
ATM_WORDS = re.compile(r"\b(atm|cash withdrawal|cash wdl)\b", re.I)
BUSINESS_WORDS = {
    "ltd", "limited", "pvt", "private", "llp", "inc", "co", "company", "corp", "enterprises",
    "traders", "trading", "agency", "agencies", "store", "stores", "shop", "mart", "foods",
    "services", "solutions", "technologies", "india", "hotel", "centre", "center", "bhavan",
}


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


# Longest key first, so "amazon prime" is tried before "amazon".
_RULES = sorted(
    ((key, category) for category, keys in MERCHANTS.items() for key in keys),
    key=lambda item: len(_compact(item[0])),
    reverse=True,
)
_MATCHERS = [
    (_compact(key), re.compile(rf"\b{re.escape(key)}\b"), category) for key, category in _RULES
]


def match_merchant(payee: str) -> str | None:
    """Category from the rules, or None if no rule applies.

    Long keys match inside joined-up names (SWIGGYLIMITED); short keys must be
    whole words, so "ola" doesn't match "kolar stores".
    """
    if not isinstance(payee, str):
        return None
    text, compact = payee.lower(), _compact(payee)
    for key, whole_word, category in _MATCHERS:
        if (len(key) >= 5 and key in compact) or whole_word.search(text):
            return category
    return None


def looks_like_person(payee: str) -> bool:
    """'priya k' or 'arjun kumar' yes; 'kumar stores' or 'unknown' no."""
    words = str(payee).lower().split()
    return (
        1 <= len(words) <= 3
        and payee != "unknown"
        and all(w.isalpha() for w in words)
        and not BUSINESS_WORDS.intersection(words)
    )


@lru_cache(maxsize=1)
def load_model(path: Path = MODEL_PATH):
    """The trained pipeline, or None so the app can still run on rules alone."""
    try:
        return joblib.load(path)
    except Exception:  # missing file or a scikit-learn version mismatch
        return None


def _regular_senders(df: pd.DataFrame) -> set[str]:
    """People who send a sizeable amount in 3+ different months (pocket money)."""
    credits = df[(df["credit"] > 0) & (df["payee"] != "unknown")]
    if credits.empty:
        return set()
    stats = credits.groupby("payee").agg(
        months=("date", lambda d: d.dt.to_period("M").nunique()),
        typical=("credit", "median"),
    )
    return set(stats[(stats["months"] >= 3) & (stats["typical"] >= 1000)].index)


def categorize(df: pd.DataFrame, model="auto") -> pd.DataFrame:
    """Add category, source, confidence and needs_review columns."""
    out = df.copy()
    if model == "auto":
        model = load_model()
    regular = _regular_senders(out)

    results: list[tuple[str, str, float, bool]] = []
    to_predict: list[int] = []
    for pos, row in enumerate(out.itertuples(index=False)):
        text = f"{row.payee} {row.description}"
        merchant = match_merchant(row.payee)
        if row.credit > 0:
            if INCOME_WORDS.search(text) or row.payee in regular:
                results.append((INCOME, "rule", 1.0, False))
            elif merchant:                         # a refund from a shop
                results.append((merchant, "rule", 1.0, False))
            else:
                results.append((TRANSFERS, "rule", 1.0, False))
        elif ATM_WORDS.search(text):
            results.append((TRANSFERS, "rule", 1.0, False))
        elif merchant:
            results.append((merchant, "rule", 1.0, False))
        else:
            results.append((TRANSFERS, "fallback", 0.0, True))
            to_predict.append(pos)

    if to_predict:
        payees = out["payee"].iloc[to_predict].tolist()
        if model is not None:
            probabilities = model.predict_proba(payees)
            for pos, payee, probs in zip(to_predict, payees, probabilities):
                best = int(probs.argmax())
                confidence = float(probs[best])
                if confidence >= MIN_CONFIDENCE:
                    results[pos] = (str(model.classes_[best]), "model", confidence, False)
                elif looks_like_person(payee):
                    results[pos] = (TRANSFERS, "person", confidence, False)
                else:
                    results[pos] = (str(model.classes_[best]), "model", confidence, True)
        else:
            for pos, payee in zip(to_predict, payees):
                if looks_like_person(payee):
                    results[pos] = (TRANSFERS, "person", 0.0, False)

    out["category"] = [r[0] for r in results]
    out["source"] = [r[1] for r in results]
    out["confidence"] = [round(r[2], 3) for r in results]
    out["needs_review"] = [r[3] for r in results]
    return out

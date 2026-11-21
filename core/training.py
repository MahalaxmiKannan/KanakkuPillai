"""Shared training and evaluation code used by notebooks/train_categorizer.ipynb."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

from core.categorizer import CATEGORIES, INCOME, TRANSFERS, match_merchant

NO_RULE = "(no rule matched)"


def build_pipeline() -> Pipeline:
    """Character n-grams cope with misspelt and cut-off merchant names."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=3000, C=10, class_weight="balanced")),
    ])


def group_split(data: pd.DataFrame, seed: int = 42, n_splits: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split (1/n_splits held out, 20% by default) that keeps every spelling of a merchant on the same side.

    Without this, 'kumar stores' in training and 'kumar store' in the test set
    would make the score look better than it really is.
    """
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    train_idx, test_idx = next(splitter.split(data, data["category"], data["merchant_group"]))
    return data.iloc[train_idx], data.iloc[test_idx]


def load_real_labels(path: Path) -> pd.DataFrame:
    """Your hand-labelled rows, ready for training. Empty if the file isn't there."""
    columns = ["payee", "category", "merchant_group", "source"]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    real = pd.read_csv(path, dtype=str).dropna(subset=["payee", "label"])
    real = real[real["label"].str.strip() != ""]
    canonical = {c.lower(): c for c in CATEGORIES}        # "rent" -> "Rent"
    real["label"] = real["label"].str.strip().str.lower().map(canonical)
    real = real.dropna(subset=["label"])                    # drop labels that aren't categories
    real = real[~real["label"].isin([INCOME, TRANSFERS])]   # people's names never go into the model
    real = real[real["payee"].str.strip().str.lower() != "unknown"]   # no name to learn from
    return pd.DataFrame({
        "payee": real["payee"].str.lower().str.strip(),
        "category": real["label"],
        "merchant_group": "real:" + real["payee"].str.lower().str.strip(),
        "source": "real",
    }).reset_index(drop=True)


def _scores(truth, predicted) -> dict:
    return {
        "accuracy": round(float(accuracy_score(truth, predicted)), 3),
        "macro_f1": round(float(f1_score(truth, predicted, average="macro", zero_division=0)), 3),
        "rows": len(truth),
    }


def evaluate(model: Pipeline, test: pd.DataFrame) -> dict:
    """Compare rules alone with rules + ML on the same held-out rows."""
    payees = test["payee"].tolist()
    truth = test["category"].tolist()
    rules = [match_merchant(p) for p in payees]
    combined = [r or m for r, m in zip(rules, model.predict(payees))]
    return {
        "rules_only": _scores(truth, [r or NO_RULE for r in rules]),
        "rules_plus_ml": _scores(truth, combined),
        "rule_coverage": round(sum(r is not None for r in rules) / len(rules), 3),
    }

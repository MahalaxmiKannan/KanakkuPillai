"""Train and evaluate the scam checker. Used by notebooks/train_scam_checker.ipynb.

Train on the synthetic messages only; the real messages are a held-out test set that the model never sees.
Synthetic scores are for development only and are never reported.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from core.scam_detector import LOW_BELOW, build_model, find_flags, level_for, rule_score

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "scam_messages.csv"


def load_messages(path: Path = DATA_FILE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(synthetic training rows, real held-out rows)."""
    df = pd.read_csv(path)
    return df[df["source"] == "synthetic"].reset_index(drop=True), df[df["source"] == "real"].reset_index(drop=True)


def _metrics(truth: np.ndarray, flagged: np.ndarray) -> dict:
    tp = int(((flagged == 1) & (truth == 1)).sum()); fp = int(((flagged == 1) & (truth == 0)).sum())
    fn = int(((flagged == 0) & (truth == 1)).sum()); tn = int(((flagged == 0) & (truth == 0)).sum())
    recall = tp / (tp + fn) if tp + fn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"recall": round(recall, 3), "precision": round(precision, 3), "f1": round(f1, 3),
            "accuracy": round((tp + tn) / len(truth), 3), "tp": tp, "fp": fp, "fn": fn, "tn": tn, "rows": int(len(truth))}


def score_messages(texts: list[str], probs: np.ndarray) -> pd.DataFrame:
    """Rule score, model probability and the combined score (same formula as the app) for each message."""
    rs = np.array([rule_score(find_flags(t)) for t in texts])
    combined = 1 - (1 - rs) * (1 - 0.75 * probs)
    return pd.DataFrame({"rule_score": rs, "model_prob": probs, "score": combined,
                         "level": [level_for(s) for s in combined],
                         "flags": [", ".join(f.name for f in find_flags(t)) for t in texts]})


def compare(truth: np.ndarray, scored: pd.DataFrame) -> dict:
    """Flagged means Medium or High. Rules only, model only (p >= 0.5) and the combined checker."""
    return {
        "rules_only": _metrics(truth, (scored["rule_score"] >= LOW_BELOW).astype(int).values),
        "model_only": _metrics(truth, (scored["model_prob"] >= 0.5).astype(int).values),
        "combined": _metrics(truth, (scored["score"] >= LOW_BELOW).astype(int).values),
    }


def grouped_cv(train: pd.DataFrame, seed: int = 42) -> dict:
    """Out-of-fold scores on the synthetic set, grouped by template so a template never sits on both sides."""
    probs = np.zeros(len(train))
    folds = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in folds.split(train["text"], train["label"], train["template_group"]):
        model = build_model().fit(train["text"].iloc[tr], train["label"].iloc[tr])
        probs[te] = model.predict_proba(train["text"].iloc[te])[:, 1]
    return compare(train["label"].values, score_messages(train["text"].tolist(), probs))

"""Turn data/nifty50_history.csv (daily, from yfinance ^NSEI) into data/nifty_monthly.csv.

Run from the repo root:  python scripts/make_nifty_monthly.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.simulator import DAILY_FILE, MONTHLY_FILE, daily_to_monthly  # noqa: E402

monthly = daily_to_monthly(pd.read_csv(DAILY_FILE))
monthly.to_csv(MONTHLY_FILE, index=False)
print(f"{len(monthly)} monthly returns, {monthly['month'].iloc[0]} to {monthly['month'].iloc[-1]} -> {MONTHLY_FILE.name}")

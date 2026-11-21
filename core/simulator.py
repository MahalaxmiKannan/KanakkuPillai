"""SIP Monte Carlo on real Nifty 50 history, plus a backtest of how honest its ranges are.

Method: block bootstrap. Each simulated path is built by gluing together random
12-month blocks of real monthly Nifty returns. Blocks keep the streaks (crashes,
recoveries) that picking single months at random would destroy, and using real
returns keeps the fat tails a normal distribution would hide.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DAILY_FILE = ROOT / "data" / "nifty50_history.csv"
MONTHLY_FILE = ROOT / "data" / "nifty_monthly.csv"

BLOCK = 12
PATHS = 10_000
PERCENTILES = (10, 50, 90)


def daily_to_monthly(daily: pd.DataFrame, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Month-end closes and monthly returns. Drops the last month unless it is finished.

    The last month counts as finished only if `as_of` (default: today) is in a later
    month AND the data reaches its final week. Checking against the last weekday
    alone would wrongly drop a full month whose last weekday was a market holiday.
    """
    d = daily[["Date", "Close"]].dropna().copy()
    d["Date"] = pd.to_datetime(d["Date"])
    d = d.sort_values("Date")
    month_end = d.groupby(d["Date"].dt.to_period("M")).last()
    last_day = d["Date"].iloc[-1]
    as_of = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.today()
    month_over = as_of.to_period("M") > last_day.to_period("M")
    reaches_final_week = last_day >= last_day + pd.offsets.MonthEnd(0) - pd.Timedelta(days=6)
    if not (month_over and reaches_final_week):
        month_end = month_end.iloc[:-1]
    out = pd.DataFrame({"month": month_end.index.astype(str), "close": month_end["Close"].round(2).values})
    out["return"] = out["close"].pct_change()
    return out.dropna().reset_index(drop=True)


def load_monthly_returns(path: Path = MONTHLY_FILE) -> pd.DataFrame:
    return pd.read_csv(path)


def sip_path(returns: np.ndarray, monthly: float) -> np.ndarray:
    """Portfolio value at the end of each month. Money goes in at the start of the month.

    returns can be 1-D (one path) or 2-D (paths x months).
    """
    r = np.atleast_2d(returns)
    values = np.empty_like(r, dtype=float)
    v = np.zeros(r.shape[0])
    for t in range(r.shape[1]):
        v = (v + monthly) * (1 + r[:, t])
        values[:, t] = v
    return values if returns.ndim == 2 else values[0]


def bootstrap_returns(returns: np.ndarray, months: int, paths: int = PATHS, block: int = BLOCK,
                      seed: int | None = 42) -> np.ndarray:
    """paths x months matrix of returns made of random real `block`-month stretches."""
    rng = np.random.default_rng(seed)
    n_blocks = -(-months // block)
    starts = rng.integers(0, len(returns) - block + 1, size=(paths, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)).reshape(paths, -1)[:, :months]
    return returns[idx]


def fixed_rate_path(months: int, monthly: float, annual_rate: float) -> np.ndarray:
    """Same SIP into something that grows at a fixed yearly rate (e.g. an FD or RD)."""
    r = (1 + annual_rate) ** (1 / 12) - 1
    return sip_path(np.full(months, r), monthly)


def simulate(monthly: float, years: int, returns: np.ndarray, inflation: float | None = None,
             fd_rate: float = 0.07, paths: int = PATHS, seed: int | None = 42) -> dict:
    """Run the Monte Carlo. With inflation set, every rupee figure is in today's money."""
    months = years * 12
    values = sip_path(bootstrap_returns(returns, months, paths, seed=seed), monthly)
    fd = fixed_rate_path(months, monthly, fd_rate)
    invested = monthly * np.arange(1, months + 1)
    # "Did I lose money?" is about rupees put in vs rupees out, so judge it before inflation.
    below_invested = float((values[:, -1] < invested[-1]).mean())
    below_fd = float((values[:, -1] < fd[-1]).mean())
    if inflation:
        deflator = (1 + inflation) ** (np.arange(1, months + 1) / 12)
        values, fd = values / deflator, fd / deflator
    bands = np.percentile(values, PERCENTILES, axis=0)
    return {
        "months": months,
        "bands": {p: bands[i] for i, p in enumerate(PERCENTILES)},
        "invested": invested,
        "fd": fd,
        "final": {p: float(bands[i][-1]) for i, p in enumerate(PERCENTILES)},
        "total_invested": float(invested[-1]),
        "chance_below_invested": below_invested,
        "chance_below_fd": below_fd,
    }


def backtest(returns: np.ndarray, years: int, paths: int = PATHS, seed: int = 42) -> dict:
    """For every real (overlapping) window of `years`, does the real SIP outcome land in the 10-90 band?

    Works with value / money put in, so the monthly amount doesn't matter. Note the
    bootstrap draws from the same history, so this is an in-sample check.
    """
    months = years * 12
    final = sip_path(bootstrap_returns(returns, months, paths, seed=seed), 1.0)[:, -1] / months
    low, high = np.percentile(final, [10, 90])
    actual = np.array([sip_path(returns[s:s + months], 1.0)[-1] / months
                       for s in range(len(returns) - months + 1)])
    return {
        "years": years,
        "windows": int(len(actual)),
        "non_overlapping": int(len(returns) // months),
        "band_10": round(float(low), 3),
        "band_90": round(float(high), 3),
        "coverage": round(float(((actual >= low) & (actual <= high)).mean()), 3),
        "below_band": round(float((actual < low).mean()), 3),
        "above_band": round(float((actual > high).mean()), 3),
    }

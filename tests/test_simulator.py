import numpy as np
import pandas as pd

from core.simulator import (bootstrap_returns, backtest, daily_to_monthly, fixed_rate_path,
                            load_monthly_returns, simulate, sip_path)


def test_sip_path_zero_returns_is_money_put_in():
    assert np.allclose(sip_path(np.zeros(12), 100), np.arange(1, 13) * 100)


def test_sip_path_money_goes_in_at_start_of_month():
    assert np.isclose(sip_path(np.array([0.10]), 100)[0], 110)


def test_fixed_rate_one_year_lump_matches_rate():
    # Instalment k sits for k months, so the first one grows by exactly the yearly rate.
    expected = sum(100 * 1.07 ** (k / 12) for k in range(1, 13))
    assert np.isclose(fixed_rate_path(12, 100, 0.07)[-1], expected)


def test_bootstrap_uses_real_blocks_in_order():
    returns = np.arange(30, dtype=float)
    out = bootstrap_returns(returns, 24, paths=50, seed=1)
    assert out.shape == (50, 24)
    assert (np.diff(out[:, :12], axis=1) == 1).all()   # each 12-month block is a real consecutive stretch
    assert np.isin(out, returns).all()


def test_daily_to_monthly_drops_unfinished_month():
    days = pd.bdate_range("2026-01-01", "2026-03-10")
    daily = pd.DataFrame({"Date": days, "Close": np.linspace(100, 120, len(days))})
    m = daily_to_monthly(daily)
    assert list(m["month"]) == ["2026-02"]                  # Jan has no prior month, Mar isn't finished


def test_simulate_shapes_and_order():
    r = load_monthly_returns()["return"].to_numpy()
    s = simulate(1000, 5, r, paths=2000)
    assert s["total_invested"] == 60_000
    assert s["final"][10] < s["final"][50] < s["final"][90]
    assert len(s["bands"][50]) == s["months"] == 60
    assert 0 <= s["chance_below_invested"] <= 1


def test_inflation_lowers_values_but_not_loss_chance():
    r = load_monthly_returns()["return"].to_numpy()
    nominal = simulate(1000, 10, r, paths=2000)
    real = simulate(1000, 10, r, inflation=0.06, paths=2000)
    assert real["final"][50] < nominal["final"][50]
    assert real["chance_below_invested"] == nominal["chance_below_invested"]


def test_history_file_is_complete():
    m = load_monthly_returns()
    assert len(m) >= 200 and m["return"].notna().all()
    assert m["return"].abs().max() < 0.4                     # no bad splices


def test_backtest_reports_coverage():
    r = load_monthly_returns()["return"].to_numpy()
    b = backtest(r, 3, paths=2000)
    assert b["windows"] == len(r) - 36 + 1
    assert 0 <= b["coverage"] <= 1

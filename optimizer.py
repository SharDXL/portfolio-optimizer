"""
Portfolio Optimizer — core data + mean-variance optimization engine.

Universe is deliberately DACH-consistent with the rest of this portfolio: eight DAX
constituents spanning different sectors, one euro government bond ETF, and one gold
ETC — a realistic long-only, multi-asset-class universe rather than a toy example.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

# Risk-free rate held consistent with the BMW DCF project's WACC assumption
# (German 10Y Bund) so the two projects don't quietly use different "risk-free" numbers.
RISK_FREE_RATE = 0.0296

UNIVERSE = {
    "SAP.DE": "SAP (Software)",
    "SIE.DE": "Siemens (Industrials)",
    "ALV.DE": "Allianz (Insurance)",
    "BAS.DE": "BASF (Chemicals)",
    "BMW.DE": "BMW (Automotive)",
    "DBK.DE": "Deutsche Bank (Banking)",
    "ADS.DE": "Adidas (Consumer)",
    "MUV2.DE": "Munich Re (Reinsurance)",
    "EXHA.DE": "iShares Core Euro Govt Bond UCITS ETF (Fixed Income)",
    "4GLD.DE": "Xetra-Gold (Gold / Alternative)",
}


def fetch_prices(period="5y"):
    """Pull adjusted close prices for the full universe and cache to CSV."""
    data = yf.download(list(UNIVERSE.keys()), period=period, progress=False)["Close"]
    data = data.ffill().dropna()
    data.to_csv("data/prices.csv")
    return data


def load_prices():
    return pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)


def portfolio_performance(weights, mean_returns, cov_matrix):
    ret = float(np.dot(weights, mean_returns))
    vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))
    return ret, vol


def _neg_sharpe(weights, mean_returns, cov_matrix, rf):
    ret, vol = portfolio_performance(weights, mean_returns, cov_matrix)
    return -(ret - rf) / vol


def _vol_only(weights, mean_returns, cov_matrix):
    return portfolio_performance(weights, mean_returns, cov_matrix)[1]


def optimize_max_sharpe(mean_returns, cov_matrix, rf=RISK_FREE_RATE):
    n = len(mean_returns)
    bounds = tuple((0, 1) for _ in range(n))  # long-only, no leverage
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)
    init = np.array([1 / n] * n)
    result = minimize(
        _neg_sharpe, init, args=(mean_returns, cov_matrix, rf),
        method="SLSQP", bounds=bounds, constraints=constraints,
    )
    return result.x


def optimize_min_variance(mean_returns, cov_matrix):
    n = len(mean_returns)
    bounds = tuple((0, 1) for _ in range(n))
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)
    init = np.array([1 / n] * n)
    result = minimize(
        _vol_only, init, args=(mean_returns, cov_matrix),
        method="SLSQP", bounds=bounds, constraints=constraints,
    )
    return result.x


def equal_weight(n):
    return np.array([1 / n] * n)


def efficient_frontier(mean_returns, cov_matrix, n_points=40):
    """Trace the frontier by minimizing variance for a grid of target returns."""
    n = len(mean_returns)
    bounds = tuple((0, 1) for _ in range(n))
    target_returns = np.linspace(mean_returns.min(), mean_returns.max(), n_points)
    frontier_vols = []
    frontier_weights = []
    for target in target_returns:
        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target: np.dot(w, mean_returns) - t},
        )
        init = np.array([1 / n] * n)
        result = minimize(
            _vol_only, init, args=(mean_returns, cov_matrix),
            method="SLSQP", bounds=bounds, constraints=constraints,
        )
        if result.success:
            frontier_vols.append(result.fun)
            frontier_weights.append(result.x)
        else:
            frontier_vols.append(np.nan)
            frontier_weights.append(np.full(n, np.nan))
    return target_returns, np.array(frontier_vols), frontier_weights


def random_portfolios(mean_returns, cov_matrix, n_portfolios=3000, rf=RISK_FREE_RATE):
    """Cloud of random long-only portfolios, for context behind the frontier."""
    n = len(mean_returns)
    results = np.zeros((3, n_portfolios))
    rng = np.random.default_rng(42)
    for i in range(n_portfolios):
        w = rng.random(n)
        w /= w.sum()
        ret, vol = portfolio_performance(w, mean_returns, cov_matrix)
        results[0, i] = ret
        results[1, i] = vol
        results[2, i] = (ret - rf) / vol
    return results


def out_of_sample_backtest(returns, train_frac=0.7, rf=RISK_FREE_RATE):
    """
    Train weights on the first train_frac of history, then apply those FIXED weights
    to the untouched remainder. This is the honesty check: in-sample optimization
    always looks great by construction, the real question is whether it holds up.
    """
    split = int(len(returns) * train_frac)
    train, test = returns.iloc[:split], returns.iloc[split:]

    mean_train = train.mean() * 252
    cov_train = train.cov() * 252
    n = len(mean_train)

    w_sharpe = optimize_max_sharpe(mean_train, cov_train, rf)
    w_minvar = optimize_min_variance(mean_train, cov_train)
    w_eq = equal_weight(n)

    out = {}
    for name, w in [("Max Sharpe (train-derived)", w_sharpe),
                    ("Min Variance (train-derived)", w_minvar),
                    ("Equal Weight", w_eq)]:
        test_series = test.dot(w)
        cum = (1 + test_series).cumprod()
        ann_ret = cum.iloc[-1] ** (252 / len(test)) - 1
        ann_vol = test_series.std() * np.sqrt(252)
        sharpe = (ann_ret - rf) / ann_vol
        out[name] = {
            "weights": w,
            "ann_return": ann_ret,
            "ann_vol": ann_vol,
            "sharpe": sharpe,
            "cumulative_return": cum.iloc[-1] - 1,
            "cumulative_series": cum,
        }
    return out, train.index[0], train.index[-1], test.index[0], test.index[-1]

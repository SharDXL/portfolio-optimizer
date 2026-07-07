"""Runner: fetches data, optimizes, backtests, prints summary, saves charts."""

import numpy as np
from optimizer import (
    UNIVERSE, RISK_FREE_RATE, fetch_prices, load_prices,
    portfolio_performance, optimize_max_sharpe, optimize_min_variance,
    equal_weight, efficient_frontier, random_portfolios, out_of_sample_backtest,
)
from charts import chart_efficient_frontier, chart_weights_comparison, chart_oos_backtest

import os
os.makedirs("output_charts", exist_ok=True)
os.makedirs("data", exist_ok=True)


def main():
    print("Fetching prices for 10-asset DACH universe...")
    try:
        prices = fetch_prices(period="5y")
    except Exception as e:
        print(f"Live fetch failed ({e}), falling back to cached data/prices.csv")
        prices = load_prices()

    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    tickers = list(mean_returns.index)
    labels = [UNIVERSE.get(t, t) for t in tickers]
    n = len(tickers)

    print(f"\nUniverse ({n} assets, 5yr daily history, {len(returns)} trading days):")
    for t, l in zip(tickers, labels):
        print(f"  {t}: {l}")

    # --- Full-sample optimization ---
    w_sharpe = optimize_max_sharpe(mean_returns, cov_matrix, RISK_FREE_RATE)
    w_minvar = optimize_min_variance(mean_returns, cov_matrix)
    w_eq = equal_weight(n)

    print("\n=== Max Sharpe Portfolio (full 5yr sample) ===")
    ret_s, vol_s = portfolio_performance(w_sharpe, mean_returns, cov_matrix)
    for t, w in zip(labels, w_sharpe):
        if w > 0.01:
            print(f"  {t}: {w:.1%}")
    print(f"  Return: {ret_s:.2%} | Vol: {vol_s:.2%} | Sharpe: {(ret_s - RISK_FREE_RATE) / vol_s:.2f}")

    print("\n=== Min Variance Portfolio (full 5yr sample) ===")
    ret_m, vol_m = portfolio_performance(w_minvar, mean_returns, cov_matrix)
    for t, w in zip(labels, w_minvar):
        if w > 0.01:
            print(f"  {t}: {w:.1%}")
    print(f"  Return: {ret_m:.2%} | Vol: {vol_m:.2%} | Sharpe: {(ret_m - RISK_FREE_RATE) / vol_m:.2f}")

    ret_e, vol_e = portfolio_performance(w_eq, mean_returns, cov_matrix)
    print(f"\n=== Equal Weight (naive 1/N) ===")
    print(f"  Return: {ret_e:.2%} | Vol: {vol_e:.2%} | Sharpe: {(ret_e - RISK_FREE_RATE) / vol_e:.2f}")

    # --- Efficient frontier + random cloud ---
    print("\nTracing efficient frontier...")
    frontier_returns, frontier_vols, _ = efficient_frontier(mean_returns, cov_matrix, n_points=40)
    random_results = random_portfolios(mean_returns, cov_matrix, n_portfolios=3000, rf=RISK_FREE_RATE)

    chart_efficient_frontier(
        random_results, frontier_returns, frontier_vols,
        (ret_s, vol_s), (ret_m, vol_m), (ret_e, vol_e), RISK_FREE_RATE,
        "output_charts/01_efficient_frontier.html",
    )
    chart_weights_comparison(labels, w_sharpe, w_minvar, w_eq,
                              "output_charts/02_weights_comparison.html")

    # --- Out-of-sample backtest (the honesty check) ---
    print("\n=== Out-of-Sample Backtest (weights fixed on train period, applied forward) ===")
    backtest_results, tr_start, tr_end, te_start, te_end = out_of_sample_backtest(returns)
    print(f"Train: {tr_start.date()} to {tr_end.date()} | Test: {te_start.date()} to {te_end.date()}")
    for name, res in backtest_results.items():
        print(f"  {name}: OOS Return {res['ann_return']:.2%} | Vol {res['ann_vol']:.2%} | "
              f"Sharpe {res['sharpe']:.2f} | Cumulative {res['cumulative_return']:.2%}")

    chart_oos_backtest(backtest_results, "output_charts/03_oos_backtest.html")

    print("\nDone. Charts saved to output_charts/.")


if __name__ == "__main__":
    main()

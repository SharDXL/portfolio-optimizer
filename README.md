# Portfolio Optimizer — Mean-Variance Optimization on a DACH Multi-Asset Universe

Builds the efficient frontier across a 10-asset, long-only universe (eight DAX
constituents spanning different sectors, one euro government bond ETF, one gold ETC),
identifies the max-Sharpe and minimum-variance portfolios, and — critically — tests
whether either of them actually beats naive equal-weighting once you move out of sample.

---

## What This Project Does

Most student "portfolio optimizer" projects stop at plotting a nice-looking efficient
frontier and calling it done. This one goes one step further: it takes the optimal
weights derived from historical data and asks the uncomfortable question — do they
still look optimal on data the optimizer never saw? That out-of-sample check is the
difference between a textbook exercise and something that reflects how mean-variance
optimization actually behaves in practice.

**The core question this project answers:** does optimizing a portfolio using
historical returns and covariances actually produce a better forward-looking portfolio
than simply splitting your capital evenly — or does it just fit noise?

---

## Setup

```bash
pip install -r requirements.txt
python analysis.py
```

---

## Project Structure

```
Portfolio_Optimizer/
├── data/
│   └── prices.csv              # 5yr daily close prices, 10-asset universe
├── optimizer.py                 # Data fetch, mean-variance engine, frontier, backtest
├── charts.py                    # 3 Plotly visualisations
├── analysis.py                  # Runner — prints full output, saves charts
└── output_charts/                # Generated HTML charts (after running)
```

---

## The Universe

| Ticker | Asset | Role |
|---|---|---|
| SAP.DE | SAP | Software |
| SIE.DE | Siemens | Industrials |
| ALV.DE | Allianz | Insurance |
| BAS.DE | BASF | Chemicals |
| BMW.DE | BMW | Automotive |
| DBK.DE | Deutsche Bank | Banking |
| ADS.DE | Adidas | Consumer |
| MUV2.DE | Munich Re | Reinsurance |
| EXHA.DE | iShares Core € Govt Bond UCITS ETF | Fixed income |
| 4GLD.DE | Xetra-Gold | Gold / alternative |

Deliberately kept consistent with the rest of this portfolio (DAX-focused, euro-
denominated) rather than switching to a generic US/global universe — the point is to
demonstrate portfolio construction on the same market this whole project series
already covers, not to start a new geography from scratch.

---

## Key Design Decisions

**1. Long-only, no leverage.** Weights are constrained to [0, 1] summing to 1 — no
short positions, no leverage. This is the realistic constraint set for an individual
investor or most retail-facing mandates, not an unconstrained academic optimization.

**2. Risk-free rate held consistent with the BMW DCF project.** Uses the German 10-year
Bund yield (2.96%) as the risk-free rate for Sharpe ratio calculations — the same
assumption used as the risk-free proxy in the [BMW DCF Valuation](../BMW_Equity_Research/P4_BMW_DCF_Valuation/)
project, so the two projects don't quietly use inconsistent "risk-free rate" numbers.

**3. Five years of daily history, not one.** A longer estimation window reduces (but
doesn't eliminate) the sensitivity of mean-variance optimization to a lucky or unlucky
recent stretch. It's still not enough to fully solve the core problem — see below.

**4. Out-of-sample backtest is the actual point of the project, not an afterthought.**
Weights are derived once on a training period (2021-07-08 to 2024-12-30) and then held
fixed and applied forward to a completely untouched test period (2025-01-02 to
2026-07-07) — no re-optimizing, no peeking. This is the only honest way to check
whether optimization adds value.

---

## Headline Output (Full 5-Year Sample)

| Strategy | Return | Volatility | Sharpe |
|---|---|---|---|
| Max Sharpe | 21.1% | 12.8% | 1.42 |
| Min Variance | 0.2% | 4.1% | -0.68 |
| Equal Weight (naive) | 12.5% | 15.9% | 0.60 |

At first glance the Max Sharpe portfolio looks dramatically better than naive
diversification. **It should be treated with real suspicion, not excitement** — see
below for why.

---

## The Honest Part — What Happens Out of Sample

The Max Sharpe portfolio above is 55.7% Xetra-Gold, with the rest split across Munich
Re, Deutsche Bank, and Allianz. A single-asset weight that large is the first red flag:
unconstrained (or lightly constrained) mean-variance optimization is notorious for
producing concentrated, corner-solution portfolios that look optimal mathematically but
would make almost no real allocator comfortable — a textbook illustration of what
Richard Michaud called "optimization enhances errors": small estimation errors in
expected returns get amplified into large, extreme position sizes.

The out-of-sample backtest confirms this concretely. Weights derived on the training
period (2021-2024) were fixed and applied to the test period (2025-2026):

| Strategy (train-derived weights) | OOS Return | OOS Volatility | OOS Sharpe |
|---|---|---|---|
| Max Sharpe | 16.1% | 16.1% | 0.82 |
| Min Variance | 4.9% | 3.8% | 0.50 |
| Equal Weight | 13.5% | 16.3% | 0.64 |

The in-sample Sharpe of 1.42 for the Max Sharpe portfolio **degrades to 0.82**
out-of-sample — a real, expected drop, since the optimizer was fit to exactly the data
that produced that 1.42 figure and inevitably captured some noise along with the
signal. **The more useful and more nuanced finding is that it still beats equal-weight
out of sample (0.82 vs. 0.64)** — so optimization wasn't worthless here, it just wasn't
nearly as good as its own backtest made it look. That's a meaningfully different, more
credible claim than either "optimization doesn't work" or "optimization found the best
portfolio."

**Why this matters more than the headline Sharpe ratio:** a portfolio-construction
project that only shows the in-sample frontier is presenting an inflated, backward-
looking result as if it were predictive. Showing the degradation — and explaining why
it happens (estimation error in expected returns, not a bug) — is the difference between
demonstrating that you can run `scipy.optimize` and demonstrating that you understand
what mean-variance optimization actually does and doesn't tell you.

---

## Output Charts

| Chart | File | What It Shows |
|-------|------|----------------|
| Efficient Frontier | `01_efficient_frontier.html` | Random portfolio cloud, frontier, and the three named portfolios plotted together |
| Weights Comparison | `02_weights_comparison.html` | Side-by-side allocation across all three strategies |
| Out-of-Sample Backtest | `03_oos_backtest.html` | Cumulative performance of train-derived weights, applied forward, un-touched |

---

## What Comes Next

**Possible extension:** constrain maximum single-asset weight (e.g. 20-25%) and re-run
the optimization and backtest — this is the standard practitioner fix for the
concentration problem above, and comparing constrained vs. unconstrained out-of-sample
performance would be a natural, still-honest follow-up rather than a new project.

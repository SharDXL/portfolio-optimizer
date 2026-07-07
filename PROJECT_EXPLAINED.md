# Portfolio Optimizer — Project Explained

**Study guide for interviews, portfolio walkthroughs, and technical questions.**

---

## What This Project Is

A mean-variance portfolio optimizer (Markowitz framework) across a 10-asset, long-only,
DACH-focused universe — eight DAX constituents across different sectors, one euro
government bond ETF, one gold ETC. Finds the maximum-Sharpe and minimum-variance
portfolios, plots the efficient frontier, and — the part that makes it different from a
template exercise — runs a genuine out-of-sample backtest to check whether the
"optimal" portfolio actually holds up once you stop looking at the data it was built on.

---

## Concepts You Must Know Cold

### 1. What is mean-variance optimization actually doing?

For a given level of risk (volatility), find the asset weights that maximize expected
return — or equivalently, for a given expected return, find the weights that minimize
risk. Do this across a whole range of target returns and you get the **efficient
frontier**: the set of portfolios where you can't get more return without taking more
risk. Any portfolio not on the frontier is leaving return on the table for the risk it's
taking.

### 2. Why the Sharpe ratio, and what "Max Sharpe" actually means

Sharpe ratio = (portfolio return − risk-free rate) / portfolio volatility. It measures
return per unit of risk. The **Max Sharpe portfolio** is the single point on the
efficient frontier with the steepest possible line back to the risk-free rate — in
theory, the portfolio every rational investor should hold (combined with cash/leverage
to dial risk up or down), per the Capital Market Line logic in CAPM. Held the risk-free
rate consistent with the German 10Y Bund (2.96%) used in the [BMW DCF
project](../BMW_Equity_Research/P4_BMW_DCF_Valuation/) — same reasoning: term-matched to
the horizon involved, not an overnight policy rate.

### 3. Why long-only, no leverage

Real constraint, not a simplification for convenience: weights bounded [0,1] summing to
1. This matters because it changes the answer — an unconstrained optimizer would happily
short the worst-performing asset and lever up the best one, producing a portfolio no
real allocator (and certainly no retail investor) could actually hold. Long-only is the
realistic, defensible constraint set.

### 4. Why the Max Sharpe portfolio ended up 55.7% in gold — and why that's a warning sign, not a win

This is the single most important thing to understand in this project. Mean-variance
optimization is **highly sensitive to the expected-return inputs**, and expected returns
are the hardest thing in finance to estimate accurately (unlike covariances, which are
comparatively stable). Small errors in expected-return estimates get amplified by the
optimizer into large, concentrated positions — a well-documented phenomenon (Richard
Michaud's "optimization enhances errors"). Gold happened to have a strong risk-adjusted
return over this specific 5-year window, so the optimizer piled into it. That doesn't
mean gold is actually the best asset going forward — it means the optimizer is
overconfident in a pattern from one historical window.

### 5. The out-of-sample backtest — the actual point of the project

Anyone can show an in-sample efficient frontier; it will always look great because it's
fit to exactly the data being shown. The honest test: derive weights from a **training
period only** (2021-07-08 to 2024-12-30), freeze them, and apply them **unchanged** to a
completely separate **test period** (2025-01-02 to 2026-07-07) the optimizer never saw.

Result: the Max Sharpe portfolio's Sharpe ratio dropped from **1.42 in-sample to 0.82
out-of-sample** — a real, expected degradation. But it still beat the naive equal-weight
portfolio out of sample (0.82 vs. 0.64 Sharpe). **That's the actual finding**:
optimization added value, just far less than its own in-sample backtest implied. Min
Variance degraded less dramatically in absolute terms because it was optimizing for a
more stable target (volatility, not return) — 0.50 Sharpe out of sample, with much lower
realized volatility (3.8%) as intended.

### 6. Why this matters more than the numbers themselves

A project that only shows the efficient frontier is presenting an inflated, backward-
looking picture as if it were predictive — that's the mistake a lot of "vibe-coded"
finance projects make without realizing it. Showing the out-of-sample degradation, and
being able to explain *why* it happens (estimation error, not a coding bug), is what
separates "I can call `scipy.optimize.minimize`" from "I understand what this technique
actually promises and where it breaks down" — which is the more valuable thing to be
able to say in an interview.

---

## Numbers to Have Ready

- **Universe:** 10 assets — SAP, Siemens, Allianz, BASF, BMW, Deutsche Bank, Adidas,
  Munich Re, iShares Euro Govt Bond ETF, Xetra-Gold
- **Risk-free rate:** 2.96% (German 10Y Bund — same as the BMW DCF project)
- **In-sample Max Sharpe:** 21.1% return, 12.8% vol, Sharpe 1.42 (55.7% gold, 18.5% Munich Re, 12.8% Deutsche Bank, 11.8% Allianz, 1.3% Siemens)
- **In-sample Min Variance:** 0.2% return, 4.1% vol, Sharpe -0.68 (93.5% bond ETF)
- **Equal weight benchmark:** 12.5% return, 15.9% vol, Sharpe 0.60
- **Out-of-sample Max Sharpe:** Sharpe drops to 0.82 (still beats equal-weight's 0.64 OOS)
- **Out-of-sample Min Variance:** Sharpe 0.50, 3.8% realized vol

---

## Likely Interview Questions and How to Answer Them

**"Your Max Sharpe portfolio is over half gold — doesn't that seem extreme?"**
Yes, and that's flagged directly in the project rather than hidden. "That's actually the
point I wanted to demonstrate — mean-variance optimization is very sensitive to
estimate error in expected returns, and it produced a concentrated, corner-solution
portfolio that no real allocator would hold as-is. I show that explicitly rather than
presenting the optimizer's output as if it were obviously correct."

**"Does optimization actually work, based on your backtest?"**
Give the nuanced answer, not a yes/no: "Partially. The in-sample Sharpe of 1.42 dropped
to 0.82 out of sample — a real degradation from fitting noise. But it still beat naive
equal-weighting out of sample, 0.82 versus 0.64. So the honest conclusion is that
optimization added value here, just much less than its own backtest suggested it would."

**"How would you fix the concentration problem?"**
"Add a maximum single-asset weight constraint — say 20-25% — and re-run both the
optimization and the out-of-sample backtest. That's the standard practitioner response
to this exact issue, and comparing constrained versus unconstrained OOS performance
would be the natural next step, not a new project."

**"Why hold the risk-free rate consistent with your BMW DCF project?"**
"Two projects in the same portfolio quietly using different 'risk-free rate' numbers
would be a real inconsistency if anyone compared them side by side — using the same
German 10Y Bund figure keeps the whole portfolio internally consistent, and it's the
economically correct choice for both: term-matched to a multi-year horizon rather than
an overnight policy rate."

**"What's the biggest limitation of this project as built?"**
"No transaction costs or rebalancing costs are modeled, and the backtest uses a single
train/test split rather than rolling windows — a more rigorous version would do a
walk-forward analysis with periodic re-optimization and transaction cost drag included,
which would likely erode the Max Sharpe portfolio's edge over equal-weight even
further."

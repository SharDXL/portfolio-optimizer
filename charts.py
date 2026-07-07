"""Three Plotly visualisations for the Portfolio Optimizer project."""

import plotly.graph_objects as go
import numpy as np


def chart_efficient_frontier(random_results, frontier_returns, frontier_vols,
                              sharpe_point, minvar_point, eq_point, rf, out_path):
    fig = go.Figure()

    # Cloud of random long-only portfolios for context
    fig.add_trace(go.Scatter(
        x=random_results[1] * 100, y=random_results[0] * 100,
        mode="markers",
        marker=dict(size=4, color=random_results[2], colorscale="Viridis",
                    showscale=True, colorbar=dict(title="Sharpe")),
        name="Random long-only portfolios",
        opacity=0.5,
    ))

    # Efficient frontier line
    fig.add_trace(go.Scatter(
        x=np.array(frontier_vols) * 100, y=np.array(frontier_returns) * 100,
        mode="lines", line=dict(color="black", width=3),
        name="Efficient frontier",
    ))

    # Key portfolios
    for label, (ret, vol), color, symbol in [
        ("Max Sharpe", sharpe_point, "red", "star"),
        ("Min Variance", minvar_point, "blue", "diamond"),
        ("Equal Weight (naive)", eq_point, "orange", "circle"),
    ]:
        fig.add_trace(go.Scatter(
            x=[vol * 100], y=[ret * 100], mode="markers+text",
            marker=dict(size=16, color=color, symbol=symbol, line=dict(width=2, color="black")),
            text=[label], textposition="top center", name=label,
        ))

    fig.add_hline(y=rf * 100, line_dash="dot", line_color="gray",
                  annotation_text=f"Risk-free rate ({rf:.2%}, German 10Y Bund)")

    fig.update_layout(
        title="Efficient Frontier — Long-Only, 10-Asset DACH Universe (5yr history)",
        xaxis_title="Annualised Volatility (%)",
        yaxis_title="Annualised Expected Return (%)",
        template="plotly_white", width=950, height=650,
    )
    fig.write_html(out_path)


def chart_weights_comparison(universe_labels, w_sharpe, w_minvar, w_eq, out_path):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Max Sharpe", x=universe_labels, y=w_sharpe * 100, marker_color="red"))
    fig.add_trace(go.Bar(name="Min Variance", x=universe_labels, y=w_minvar * 100, marker_color="blue"))
    fig.add_trace(go.Bar(name="Equal Weight", x=universe_labels, y=w_eq * 100, marker_color="orange"))
    fig.update_layout(
        title="Portfolio Weights by Strategy",
        yaxis_title="Weight (%)", barmode="group",
        template="plotly_white", width=1000, height=600,
        xaxis_tickangle=-35,
    )
    fig.write_html(out_path)


def chart_oos_backtest(backtest_results, out_path):
    fig = go.Figure()
    colors = {"Max Sharpe (train-derived)": "red", "Min Variance (train-derived)": "blue",
              "Equal Weight": "orange"}
    for name, res in backtest_results.items():
        series = res["cumulative_series"]
        fig.add_trace(go.Scatter(
            x=series.index, y=(series - 1) * 100, mode="lines",
            name=f"{name} (Sharpe {res['sharpe']:.2f})",
            line=dict(color=colors.get(name, "gray"), width=2.5),
        ))
    fig.update_layout(
        title="Out-of-Sample Backtest — Weights Fixed on Training Period, Applied Forward",
        xaxis_title="Date", yaxis_title="Cumulative Return (%)",
        template="plotly_white", width=1000, height=600,
    )
    fig.write_html(out_path)

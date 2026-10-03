from __future__ import annotations

import pandas as pd


def calculate_volatility(price_data: pd.DataFrame) -> float:
    """Calculate annualised volatility from daily closing prices."""
    returns = price_data["Close"].pct_change().dropna()

    if returns.empty:
        return 0.0

    return returns.std() * (252 ** 0.5)


def calculate_max_drawdown(price_data: pd.DataFrame) -> float:
    """Calculate the maximum peak-to-trough decline."""
    prices = price_data["Close"].dropna()

    if prices.empty:
        return 0.0

    running_max = prices.cummax()
    drawdowns = (prices / running_max) - 1

    return drawdowns.min()


def calculate_sharpe_ratio(
    price_data: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate annualised Sharpe ratio."""
    returns = price_data["Close"].pct_change().dropna()

    if returns.empty:
        return 0.0

    daily_risk_free_rate = risk_free_rate / 252
    excess_returns = returns - daily_risk_free_rate

    volatility = returns.std()

    if volatility == 0:
        return 0.0

    return (excess_returns.mean() / volatility) * (252 ** 0.5)
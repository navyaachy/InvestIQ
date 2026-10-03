from __future__ import annotations

import pandas as pd


def calculate_daily_returns(price_data: pd.DataFrame) -> pd.Series:
    """Calculate daily percentage returns from closing prices."""
    return price_data["Close"].pct_change().dropna()


def calculate_total_return(price_data: pd.DataFrame) -> float:
    """Calculate total return over the available period."""
    prices = price_data["Close"].dropna()

    if len(prices) < 2:
        return 0.0

    return (prices.iloc[-1] / prices.iloc[0]) - 1


def calculate_annualised_return(price_data: pd.DataFrame) -> float:
    """Calculate annualised return based on the available period."""
    prices = price_data["Close"].dropna()

    if len(prices) < 2:
        return 0.0

    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1

    days = (prices.index[-1] - prices.index[0]).days

    if days <= 0:
        return 0.0

    return (1 + total_return) ** (365 / days) - 1
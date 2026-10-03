from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf


st.set_page_config(
    page_title="InvestIQ | Historical Analysis",
    page_icon="??",
    layout="wide",
)

st.title("Historical Portfolio Analysis")
st.caption(
    "Analyse how the current portfolio holdings behaved over historical periods. "
    "This is historical analysis, not a forecast."
)

holdings = st.session_state.get("portfolio_holdings", [])

valid = []

for row in holdings:
    try:
        ticker = str(row.get("Ticker", "")).strip().upper()
        quantity = float(row.get("Quantity"))
        if ticker and quantity > 0:
            valid.append((ticker, quantity))
    except (TypeError, ValueError):
        continue

if not valid:
    st.info("Add portfolio holdings from the main InvestIQ page first.")
    st.stop()


period = st.selectbox(
    "Historical period",
    ["6mo", "1y", "2y", "5y"],
    index=1,
)

tickers = [ticker for ticker, _ in valid]

with st.spinner("Retrieving historical prices..."):
    raw = yf.download(
        tickers=tickers,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

if raw is None or raw.empty:
    st.error("Historical price data could not be retrieved.")
    st.stop()


if isinstance(raw.columns, pd.MultiIndex):
    if "Close" in raw.columns.get_level_values(0):
        prices = raw["Close"].copy()
    else:
        prices = raw["Adj Close"].copy()
else:
    prices = raw[["Close"]].copy()
    prices.columns = [tickers[0]]

prices = prices.apply(pd.to_numeric, errors="coerce").dropna(how="all")

available = [ticker for ticker in tickers if ticker in prices.columns]

if not available:
    st.error("No usable historical price data was found.")
    st.stop()

prices = prices[available].dropna(how="all")

weights_value = {}

for ticker, quantity in valid:
    if ticker in prices.columns:
        latest = prices[ticker].dropna().iloc[-1]
        weights_value[ticker] = quantity * latest

total_value = sum(weights_value.values())

if total_value <= 0:
    st.error("Portfolio value could not be calculated from historical data.")
    st.stop()

weights = {
    ticker: value / total_value
    for ticker, value in weights_value.items()
}

returns = prices.pct_change(fill_method=None)

portfolio_returns = pd.Series(0.0, index=returns.index)

for ticker, weight in weights.items():
    if ticker in returns.columns:
        portfolio_returns = portfolio_returns.add(
            returns[ticker].fillna(0) * weight,
            fill_value=0,
        )

portfolio_returns = portfolio_returns.dropna()

if len(portfolio_returns) < 2:
    st.warning("Not enough historical observations for analysis.")
    st.stop()

portfolio_growth = (1 + portfolio_returns).cumprod()
portfolio_return = portfolio_growth.iloc[-1] - 1

volatility = portfolio_returns.std() * np.sqrt(252)

drawdown = portfolio_growth / portfolio_growth.cummax() - 1
max_drawdown = drawdown.min()

benchmark = yf.download(
    "^NSEI",
    period=period,
    interval="1d",
    auto_adjust=True,
    progress=False,
)

benchmark_return = None

if benchmark is not None and not benchmark.empty:
    if isinstance(benchmark.columns, pd.MultiIndex):
        benchmark_prices = benchmark["Close"].squeeze()
    else:
        benchmark_prices = benchmark["Close"]

    benchmark_prices = pd.to_numeric(
        benchmark_prices,
        errors="coerce",
    ).dropna()

    if len(benchmark_prices) > 1:
        benchmark_return = (
            benchmark_prices.iloc[-1] /
            benchmark_prices.iloc[0]
        ) - 1


st.markdown("### Historical Performance")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Portfolio Return",
    f"{portfolio_return * 100:.2f}%",
)

c2.metric(
    "Annualised Volatility",
    f"{volatility * 100:.2f}%",
)

c3.metric(
    "Maximum Drawdown",
    f"{max_drawdown * 100:.2f}%",
)

c4.metric(
    "Observations",
    f"{len(portfolio_returns):,}",
)


st.markdown("### Portfolio Growth")

growth_display = portfolio_growth.rename("Portfolio")

st.line_chart(growth_display)


if benchmark_return is not None:
    st.markdown("### Benchmark Context")

    c1, c2 = st.columns(2)

    c1.metric(
        "Portfolio Return",
        f"{portfolio_return * 100:.2f}%",
    )

    c2.metric(
        "NIFTY 50 Return",
        f"{benchmark_return * 100:.2f}%",
    )


st.markdown("### Holding Performance")

holding_rows = []

for ticker in available:
    series = prices[ticker].dropna()

    if len(series) < 2:
        continue

    holding_return = (
        series.iloc[-1] / series.iloc[0]
    ) - 1

    holding_volatility = (
        series.pct_change()
        .dropna()
        .std()
        * np.sqrt(252)
    )

    holding_drawdown = (
        series / series.cummax() - 1
    ).min()

    holding_rows.append(
        {
            "Ticker": ticker,
            "Historical Return": f"{holding_return * 100:.2f}%",
            "Annualised Volatility": f"{holding_volatility * 100:.2f}%",
            "Maximum Drawdown": f"{holding_drawdown * 100:.2f}%",
            "Current Weight": f"{weights[ticker] * 100:.2f}%",
        }
    )

st.dataframe(
    holding_rows,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Historical Drawdown")

st.line_chart(
    drawdown.rename("Portfolio Drawdown")
)


st.markdown("### What This Means")

st.write(
    "Historical return shows how the portfolio would have behaved over the "
    "selected period using the current holding quantities and a constant "
    "portfolio-weight framework."
)

st.write(
    "Annualised volatility measures historical variability, while maximum "
    "drawdown shows the largest observed peak-to-trough decline."
)

st.caption(
    "Important: this analysis reconstructs historical behaviour from the "
    "current holdings. It does not represent the user's actual historical "
    "transactions, entry dates, realised returns, or future performance."
)

st.caption(
    "Data source: Yahoo Finance via yfinance. Missing historical prices are "
    "not estimated or silently substituted."
)

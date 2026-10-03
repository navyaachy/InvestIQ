from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf


st.set_page_config(
    page_title="InvestIQ | Stock Comparison",
    page_icon="??",
    layout="wide",
)

st.title("Stock Comparison")
st.caption("Compare multiple stocks using observed market, fundamental, growth, valuation and risk evidence.")


tickers_text = st.text_input(
    "Enter 2 to 5 stock tickers",
    value="RELIANCE.NS, TCS.NS, HDFCBANK.NS",
    help="Use Yahoo Finance tickers. Example: RELIANCE.NS, TCS.NS",
)

tickers = [
    ticker.strip().upper()
    for ticker in tickers_text.split(",")
    if ticker.strip()
]

tickers = list(dict.fromkeys(tickers))[:5]

if len(tickers) < 2:
    st.info("Enter at least 2 stock tickers to compare.")
    st.stop()


@st.cache_data(ttl=900)
def get_stock_data(tickers):
    rows = []
    histories = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            history = stock.history(
                period="1y",
                interval="1d",
                auto_adjust=True,
            )

            histories[ticker] = history

            rows.append(
                {
                    "Ticker": ticker,
                    "Price": info.get("currentPrice") or info.get("regularMarketPrice"),
                    "Market Cap": info.get("marketCap"),
                    "P/E": info.get("trailingPE"),
                    "Forward P/E": info.get("forwardPE"),
                    "P/B": info.get("priceToBook"),
                    "EV/EBITDA": info.get("enterpriseToEbitda"),
                    "Revenue Growth": info.get("revenueGrowth"),
                    "Earnings Growth": info.get("earningsGrowth"),
                    "Profit Margin": info.get("profitMargins"),
                    "ROE": info.get("returnOnEquity"),
                    "Debt/Equity": info.get("debtToEquity"),
                    "Beta": info.get("beta"),
                    "Sector": info.get("sector"),
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "Ticker": ticker,
                    "Price": None,
                    "Market Cap": None,
                    "P/E": None,
                    "Forward P/E": None,
                    "P/B": None,
                    "EV/EBITDA": None,
                    "Revenue Growth": None,
                    "Earnings Growth": None,
                    "Profit Margin": None,
                    "ROE": None,
                    "Debt/Equity": None,
                    "Beta": None,
                    "Sector": None,
                    "Error": str(exc),
                }
            )

    return pd.DataFrame(rows), histories


with st.spinner("Retrieving comparison data..."):
    comparison, histories = get_stock_data(tuple(tickers))


if comparison.empty:
    st.error("No comparison data could be retrieved.")
    st.stop()


st.markdown("### Market & Valuation")

valuation_columns = [
    "Ticker",
    "Price",
    "Market Cap",
    "P/E",
    "Forward P/E",
    "P/B",
    "EV/EBITDA",
]

valuation_df = comparison[valuation_columns].copy()

if "Market Cap" in valuation_df.columns:
    valuation_df["Market Cap"] = valuation_df["Market Cap"].apply(
        lambda x: f"?{x / 1e7:,.0f} Cr"
        if pd.notna(x)
        else "N/A"
    )

for column in ["Price"]:
    valuation_df[column] = valuation_df[column].apply(
        lambda x: f"?{x:,.2f}" if pd.notna(x) else "N/A"
    )

for column in ["P/E", "Forward P/E", "P/B", "EV/EBITDA"]:
    valuation_df[column] = valuation_df[column].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )

st.dataframe(
    valuation_df,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Growth & Fundamentals")

fundamental_columns = [
    "Ticker",
    "Revenue Growth",
    "Earnings Growth",
    "Profit Margin",
    "ROE",
    "Debt/Equity",
]

fundamental_df = comparison[fundamental_columns].copy()

for column in [
    "Revenue Growth",
    "Earnings Growth",
    "Profit Margin",
    "ROE",
]:
    fundamental_df[column] = fundamental_df[column].apply(
        lambda x: f"{x * 100:.2f}%"
        if pd.notna(x)
        else "N/A"
    )

fundamental_df["Debt/Equity"] = fundamental_df["Debt/Equity"].apply(
    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
)

st.dataframe(
    fundamental_df,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Historical Risk")

risk_rows = []

for ticker in tickers:
    history = histories.get(ticker)

    if history is None or history.empty or "Close" not in history.columns:
        risk_rows.append(
            {
                "Ticker": ticker,
                "Volatility": None,
                "Max Drawdown": None,
                "Beta": comparison.loc[
                    comparison["Ticker"] == ticker, "Beta"
                ].iloc[0]
                if not comparison.loc[
                    comparison["Ticker"] == ticker
                ].empty
                else None,
            }
        )
        continue

    prices = history["Close"].dropna()
    returns = prices.pct_change(fill_method=None).dropna()

    volatility = (
        returns.std() * np.sqrt(252)
        if len(returns) >= 20
        else None
    )

    drawdown = (
        prices / prices.cummax() - 1
        if not prices.empty
        else pd.Series(dtype=float)
    )

    max_drawdown = drawdown.min() if not drawdown.empty else None

    beta_row = comparison.loc[
        comparison["Ticker"] == ticker, "Beta"
    ]

    beta = beta_row.iloc[0] if not beta_row.empty else None

    risk_rows.append(
        {
            "Ticker": ticker,
            "Volatility": volatility,
            "Max Drawdown": max_drawdown,
            "Beta": beta,
        }
    )

risk_df = pd.DataFrame(risk_rows)

for column in ["Volatility", "Max Drawdown"]:
    risk_df[column] = risk_df[column].apply(
        lambda x: f"{x * 100:.2f}%"
        if pd.notna(x)
        else "N/A"
    )

risk_df["Beta"] = risk_df["Beta"].apply(
    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
)

st.dataframe(
    risk_df,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Sector")

sector_df = comparison[["Ticker", "Sector"]].copy()
sector_df["Sector"] = sector_df["Sector"].fillna("Unavailable")

st.dataframe(
    sector_df,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Price Performance")

performance_rows = []

for ticker in tickers:
    history = histories.get(ticker)

    if history is None or history.empty or "Close" not in history.columns:
        performance_rows.append(
            {
                "Ticker": ticker,
                "1-Year Return": None,
            }
        )
        continue

    prices = history["Close"].dropna()

    if len(prices) >= 2:
        one_year_return = prices.iloc[-1] / prices.iloc[0] - 1
    else:
        one_year_return = None

    performance_rows.append(
        {
            "Ticker": ticker,
            "1-Year Return": one_year_return,
        }
    )

performance_df = pd.DataFrame(performance_rows)

performance_df["1-Year Return"] = performance_df[
    "1-Year Return"
].apply(
    lambda x: f"{x * 100:.2f}%"
    if pd.notna(x)
    else "N/A"
)

st.dataframe(
    performance_df,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### How to Use This Comparison")

st.write(
    "Use the tables to compare valuation, growth, profitability, leverage and "
    "historical risk across the selected stocks."
)

st.write(
    "Lower or higher values are not automatically better across every metric. "
    "Interpret each metric in the context of the company's sector and business model."
)

st.caption(
    "Data source: Yahoo Finance via yfinance. Metrics reflect retrieved provider data "
    "and historical observations. This module does not provide a buy, sell or hold recommendation."
)

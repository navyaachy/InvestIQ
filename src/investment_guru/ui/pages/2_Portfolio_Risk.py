from __future__ import annotations

import streamlit as st

from src.investment_guru.analytics.portfolio_risk import build_portfolio_risk


st.set_page_config(
    page_title="InvestIQ | Portfolio Risk",
    page_icon="🛡️",
    layout="wide",
)

st.title("Portfolio Risk & Diversification")
st.caption(
    "Observed portfolio risk based on retrieved historical daily prices. "
    "This is analysis, not a buy/sell recommendation."
)

holdings = st.session_state.get("portfolio_holdings", [])

valid = []

for row in holdings:
    ticker = str(row.get("Ticker", "")).strip().upper()

    try:
        quantity = float(row.get("Quantity"))
        current_price = float(row.get("Current Price"))
    except (TypeError, ValueError):
        continue

    if ticker and quantity > 0 and current_price > 0:
        valid.append(
            {
                "Ticker": ticker,
                "Quantity": quantity,
                "Current Price": current_price,
            }
        )

if not valid:
    st.info(
        "Go to the main InvestIQ page, add your holdings, refresh portfolio "
        "prices, then return here."
    )
    st.stop()


with st.spinner("Calculating portfolio risk from 1-year daily price history..."):
    metrics = build_portfolio_risk(
        valid,
        benchmark="^NSEI",
        period="1y",
    )


if metrics.get("status") != "ok":
    st.warning(metrics.get("message", "Risk analysis is unavailable."))
    st.stop()


# ---------------------------------------------------------
# PORTFOLIO OVERVIEW
# ---------------------------------------------------------

st.markdown("### Portfolio Risk Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Holdings",
    str(metrics.get("holding_count", "N/A")),
)

largest_weight = metrics.get("largest_weight")

c2.metric(
    "Largest Holding",
    f"{largest_weight * 100:.2f}%"
    if largest_weight is not None
    else "N/A",
)

portfolio_volatility = metrics.get("portfolio_volatility")

c3.metric(
    "Annualised Volatility",
    f"{portfolio_volatility * 100:.2f}%"
    if portfolio_volatility is not None
    else "N/A",
)

portfolio_beta = metrics.get("portfolio_beta")

c4.metric(
    "Beta vs NIFTY 50",
    f"{portfolio_beta:.2f}"
    if portfolio_beta is not None
    else "N/A",
)


# ---------------------------------------------------------
# CONCENTRATION
# ---------------------------------------------------------

st.markdown("### Concentration & Diversification")

c1, c2, c3 = st.columns(3)

hhi = metrics.get("hhi")
effective_number = metrics.get("effective_number")

c1.metric(
    "Concentration Level",
    metrics.get("concentration_level", "N/A"),
)

c2.metric(
    "Effective Number of Holdings",
    f"{effective_number:.2f}"
    if effective_number is not None
    else "N/A",
)

c3.metric(
    "HHI",
    f"{hhi:.3f}"
    if hhi is not None
    else "N/A",
)


st.info(metrics.get("diversification_note", "Diversification evidence unavailable."))


# ---------------------------------------------------------
# PORTFOLIO ALLOCATION
# ---------------------------------------------------------

st.markdown("### Portfolio Allocation")

allocation_rows = []

for row in valid:
    ticker = row["Ticker"]
    quantity = row["Quantity"]
    current_price = row["Current Price"]

    current_value = quantity * current_price

    allocation_rows.append(
        {
            "Ticker": ticker,
            "Quantity": quantity,
            "Current Price": current_price,
            "Current Value": current_value,
        }
    )

if allocation_rows:
    allocation_df = st.dataframe(
        allocation_rows,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# STOCK-LEVEL RISK
# ---------------------------------------------------------

st.markdown("### Stock-Level Risk")

stock_metrics = metrics.get("stock_metrics")

if stock_metrics is not None and not stock_metrics.empty:

    display_metrics = stock_metrics.copy()

    if "Volatility" in display_metrics.columns:
        display_metrics["Volatility"] = display_metrics["Volatility"].apply(
            lambda x: f"{x * 100:.2f}%"
            if x is not None
            else "N/A"
        )

    if "Max Drawdown" in display_metrics.columns:
        display_metrics["Max Drawdown"] = display_metrics["Max Drawdown"].apply(
            lambda x: f"{x * 100:.2f}%"
            if x is not None
            else "N/A"
        )

    if "Beta" in display_metrics.columns:
        display_metrics["Beta"] = display_metrics["Beta"].apply(
            lambda x: f"{x:.2f}"
            if x is not None
            else "N/A"
        )

    st.dataframe(
        display_metrics,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("Stock-level historical risk metrics are unavailable.")


# ---------------------------------------------------------
# CORRELATION
# ---------------------------------------------------------

st.markdown("### Holding Correlation")

correlation = metrics.get("correlation")

if correlation is not None and not correlation.empty and len(correlation.columns) > 1:

    st.caption(
        "Historical correlation between portfolio holdings over the selected period."
    )

    st.dataframe(
        correlation.round(2),
        use_container_width=True,
    )

else:

    st.info(
        "Correlation analysis becomes informative when the portfolio contains "
        "multiple holdings with sufficient overlapping historical data."
    )


average_correlation = metrics.get("average_correlation")

if average_correlation is not None:
    st.metric(
        "Average Pairwise Correlation",
        f"{average_correlation:.2f}",
    )


# ---------------------------------------------------------
# RISK CONTRIBUTION
# ---------------------------------------------------------

st.markdown("### Risk Contribution")

risk_contribution = metrics.get("risk_contribution")

if risk_contribution is not None and not risk_contribution.empty:

    display_risk = risk_contribution.copy()

    if "Portfolio Weight" in display_risk.columns:
        display_risk["Portfolio Weight"] = display_risk[
            "Portfolio Weight"
        ].apply(
            lambda x: f"{x * 100:.2f}%"
        )

    if "Risk Contribution" in display_risk.columns:
        display_risk["Risk Contribution"] = display_risk[
            "Risk Contribution"
        ].apply(
            lambda x: f"{x * 100:.2f}%"
        )

    st.dataframe(
        display_risk,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "Risk contribution requires sufficient overlapping historical price data."
    )


# ---------------------------------------------------------
# INTERPRETATION
# ---------------------------------------------------------

st.markdown("### What the Numbers Mean")

st.write(
    "**Annualised volatility** measures the historical variability of portfolio "
    "returns. Higher values indicate larger historical fluctuations."
)

st.write(
    "**Maximum drawdown** measures the largest peak-to-trough decline observed "
    "for an individual holding during the analysed period."
)

st.write(
    "**Portfolio beta** describes historical sensitivity of the portfolio to the "
    "NIFTY 50 benchmark. It is not a forecast."
)

st.write(
    "**HHI and effective number of holdings** describe how concentrated the "
    "current portfolio weights are."
)

st.write(
    "**Correlation** describes how holdings have historically moved relative to "
    "one another. Lower correlation can provide more variation in historical "
    "return patterns, but does not guarantee lower future losses."
)

st.write(
    "**Risk contribution** estimates how individual holdings contributed to the "
    "portfolio's historical variance based on the selected price history."
)


# ---------------------------------------------------------
# DATA TRANSPARENCY
# ---------------------------------------------------------

st.markdown("### Data & Methodology")

st.write(
    f"**Historical period:** {metrics.get('period', 'N/A')}"
)

st.write(
    f"**Benchmark:** {metrics.get('benchmark', 'N/A')}"
)

st.caption(
    "Data source: Yahoo Finance via yfinance. Risk calculations use the latest "
    "retrieved historical daily prices available to the provider at runtime. "
    "Missing history is not estimated or silently substituted."
)
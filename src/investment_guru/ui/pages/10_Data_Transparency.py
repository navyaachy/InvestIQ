from __future__ import annotations

from datetime import datetime

import streamlit as st
import yfinance as yf

from src.investment_guru.data.data_freshness import classify_data_freshness


st.set_page_config(
    page_title="InvestIQ | Data Transparency",
    page_icon="🔎",
    layout="wide",
)

st.title("Data Transparency")
st.caption(
    "Sources, timestamps, availability, and methodology behind the "
    "information displayed by InvestIQ."
)

holdings = st.session_state.get("portfolio_holdings", [])

if not holdings:
    st.info("Add holdings from the main InvestIQ page first.")
    st.stop()


# ============================================================
# Current session timestamp
# ============================================================

session_time = datetime.now().astimezone()

st.markdown("### Current Session")

c1, c2 = st.columns(2)

with c1:
    st.metric(
        "Report Session Time",
        session_time.strftime("%d %b %Y, %H:%M:%S"),
    )

with c2:
    st.metric(
        "Holdings Tracked",
        len(holdings),
    )


st.caption(
    "Times shown here describe when InvestIQ retrieved or generated "
    "information during the current session. Market providers may "
    "themselves publish data with different timestamps."
)


# ============================================================
# Price data
# ============================================================

st.markdown("### Market Price Data")

price_rows = []

for row in holdings:

    ticker = str(row.get("Ticker", "")).strip().upper()

    if not ticker:
        continue

    source = row.get("Price Source", "Yahoo Finance")
    status = row.get("Price Status", "Available")
    retrieval = row.get("Price Retrieval Time")

    if not retrieval:
        retrieval = row.get("retrieved_at")

    if not retrieval:
        retrieval = "Not recorded in current portfolio session"

    freshness = classify_data_freshness(
        retrieval if retrieval != "Not recorded in current portfolio session" else None
    )

    price_rows.append(
        {
            "Ticker": ticker,
            "Current Price": row.get("Current Price", "Unavailable"),
            "Source": source,
            "Status": status,
            "Freshness": freshness["label"],
            "Retrieved": retrieval,
        }
    )

if price_rows:

    st.dataframe(
        price_rows,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("No market price records are available.")


# ============================================================
# Fundamental data
# ============================================================

st.markdown("### Fundamental & Valuation Data")

fundamental_rows = []

for row in holdings:

    ticker = str(row.get("Ticker", "")).strip().upper()

    if not ticker:
        continue

    try:

        info = yf.Ticker(ticker).info

        fundamental_rows.append(
            {
                "Ticker": ticker,
                "Source": "Yahoo Finance via yfinance",
                "Retrieved": session_time.strftime(
                    "%d %b %Y, %H:%M:%S"
                ),
                "P/E": (
                    info.get("trailingPE")
                    if info.get("trailingPE") is not None
                    else "Unavailable"
                ),
                "Forward P/E": (
                    info.get("forwardPE")
                    if info.get("forwardPE") is not None
                    else "Unavailable"
                ),
                "P/B": (
                    info.get("priceToBook")
                    if info.get("priceToBook") is not None
                    else "Unavailable"
                ),
                "Revenue Growth": (
                    info.get("revenueGrowth")
                    if info.get("revenueGrowth") is not None
                    else "Unavailable"
                ),
                "Profit Margin": (
                    info.get("profitMargins")
                    if info.get("profitMargins") is not None
                    else "Unavailable"
                ),
            }
        )

    except Exception as exc:

        fundamental_rows.append(
            {
                "Ticker": ticker,
                "Source": "Yahoo Finance via yfinance",
                "Retrieved": session_time.strftime(
                    "%d %b %Y, %H:%M:%S"
                ),
                "P/E": "Unavailable",
                "Forward P/E": "Unavailable",
                "P/B": "Unavailable",
                "Revenue Growth": "Unavailable",
                "Profit Margin": "Unavailable",
            }
        )


if fundamental_rows:

    st.dataframe(
        fundamental_rows,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Historical market data
# ============================================================

st.markdown("### Historical Market Data")

st.dataframe(
    [
        {
            "Dataset": "Historical prices",
            "Source": "Yahoo Finance via yfinance",
            "Purpose": "Historical performance, volatility, drawdown and beta",
            "Typical Period": "6 months to 5 years",
            "Status": "Retrieved on demand",
        },
        {
            "Dataset": "NIFTY 50 benchmark",
            "Source": "Yahoo Finance via yfinance",
            "Purpose": "Benchmark context for portfolio analysis",
            "Typical Period": "1 year",
            "Status": "Retrieved on demand",
        },
    ],
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# News
# ============================================================

st.markdown("### News Data")

st.dataframe(
    [
        {
            "Dataset": "Company news",
            "Source": "Google News RSS",
            "Purpose": "Recent company and business-event context",
            "Retrieved": session_time.strftime(
                "%d %b %Y, %H:%M:%S"
            ),
            "Status": "Retrieved on demand",
        },
    ],
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# Data availability
# ============================================================

st.markdown("### Data Freshness")

st.write(
    "InvestIQ classifies market-data freshness using the provider "
    "retrieval timestamp. During normal NSE market hours, recent "
    "observations are assessed more strictly. Outside market hours, "
    "the latest available observation is not automatically treated "
    "as stale."
)

st.caption(
    "Freshness labels describe the age of the provider observation. "
    "They do not guarantee real-time accuracy or completeness."
)


st.markdown("### Availability Rules")

st.write(
    "InvestIQ does not estimate unavailable financial metrics simply "
    "to fill a table. When the underlying provider does not supply "
    "a metric, the application labels it as unavailable."
)

st.write(
    "Provider availability can change over time. A value being displayed "
    "does not mean every provider field was retrieved at exactly the same "
    "moment."
)


# ============================================================
# Methodology
# ============================================================

st.markdown("### Source & Methodology Notes")

notes = [
    "Portfolio prices are retrieved from the configured market-price provider.",
    "Fundamental and valuation metrics are retrieved from Yahoo Finance through yfinance.",
    "Historical analysis uses historical market-price observations retrieved on demand.",
    "Portfolio risk uses historical price observations and the selected benchmark.",
    "News is retrieved separately through Google News RSS.",
    "Historical analysis reconstructs portfolio behaviour from current holdings and historical prices; it does not represent actual historical transactions.",
    "Monitoring alerts are rule-based and depend on the thresholds configured in the application.",
    "Investment analysis is descriptive and evidence-based and does not guarantee future performance.",
]

for note in notes:
    st.write(f"• {note}")


st.markdown("### Important Limitation")

st.warning(
    "External financial and news data can be delayed, revised, incomplete, "
    "or temporarily unavailable. InvestIQ surfaces provider data and "
    "availability rather than treating every observation as guaranteed real-time information."
)

st.caption(
    f"Transparency page generated at {session_time.strftime('%d %b %Y, %H:%M:%S %Z')}."
)

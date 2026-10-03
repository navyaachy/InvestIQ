from __future__ import annotations

import streamlit as st
import pandas as pd

from src.investment_guru.analytics.portfolio import (
    calculate_portfolio_summary,
    calculate_sector_exposure,
)


st.set_page_config(
    page_title="InvestIQ | Portfolio Dashboard",
    page_icon="??",
    layout="wide",
)

st.title("Portfolio Dashboard")
st.caption("A consolidated view of portfolio performance, allocation and exposure.")


holdings = st.session_state.get("portfolio_holdings", [])

if not holdings:
    st.info("Add holdings from the main InvestIQ page to build your portfolio dashboard.")
    st.stop()


summary = calculate_portfolio_summary(holdings)

if summary["holding_count"] == 0:
    st.warning("No valid portfolio holdings are currently available.")
    st.stop()


df = pd.DataFrame(summary["holdings"])

total_invested = summary["invested_value"]
total_current = summary["current_value"]
total_pnl = summary["pnl"]
total_return = summary["return_pct"]


st.markdown("### Portfolio Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Invested Value", f"?{total_invested:,.0f}")
c2.metric("Current Value", f"?{total_current:,.0f}")
c3.metric("Total P&L", f"?{total_pnl:,.0f}")
c4.metric(
    "Return",
    f"{total_return:.2f}%" if total_return is not None else "N/A",
)


st.markdown("### Holdings")

display_columns = [
    "Ticker",
    "Quantity",
    "Buy Price",
    "Current Price",
    "Invested Value",
    "Current Value",
    "P&L",
    "Return %",
    "Weight %",
]

display_df = df[display_columns].copy()

for column in ["Invested Value", "Current Value", "P&L"]:
    display_df[column] = display_df[column].apply(
        lambda x: f"?{x:,.0f}" if pd.notna(x) else "N/A"
    )

for column in ["Return %", "Weight %"]:
    display_df[column] = display_df[column].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Portfolio Allocation")

allocation = (
    df[["Ticker", "Weight %"]]
    .dropna()
    .sort_values("Weight %", ascending=False)
    .set_index("Ticker")
)

st.bar_chart(allocation["Weight %"])


st.markdown("### Sector Exposure")

sector_result = calculate_sector_exposure(summary["holdings"])

if sector_result["sectors"]:

    sector_df = pd.DataFrame(sector_result["sectors"])

    sector_display = sector_df[
        ["Sector", "Current Value", "Weight %", "Holding Count", "Holdings"]
    ].copy()

    sector_display["Current Value"] = sector_display["Current Value"].apply(
        lambda x: f"?{x:,.0f}"
    )

    sector_display["Weight %"] = sector_display["Weight %"].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
    )

    st.dataframe(
        sector_display,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("Sector exposure is unavailable.")


st.markdown("### Portfolio Concentration")

largest_weight = float(df["Weight %"].max())

effective_holdings = (
    1 / ((df["Weight %"] / 100) ** 2).sum()
    if not df.empty
    else None
)

c1, c2, c3 = st.columns(3)

c1.metric("Number of Holdings", str(len(df)))

c2.metric(
    "Largest Holding",
    f"{largest_weight:.2f}%",
)

c3.metric(
    "Effective Holdings",
    f"{effective_holdings:.2f}"
    if effective_holdings is not None
    else "N/A",
)


if largest_weight >= 50:
    st.warning(
        "A single holding represents more than half of the current portfolio value. "
        "Review concentration alongside the Portfolio Risk analysis."
    )


st.markdown("### Portfolio Interpretation")

if total_return is not None:

    if total_return > 0:
        st.write(
            f"The portfolio is currently above its recorded invested value by "
            f"?{total_pnl:,.0f}, representing a {total_return:.2f}% return."
        )

    elif total_return < 0:
        st.write(
            f"The portfolio is currently below its recorded invested value by "
            f"?{abs(total_pnl):,.0f}, representing a {abs(total_return):.2f}% decline."
        )

    else:
        st.write(
            "The portfolio is currently at its recorded invested value."
        )


st.caption(
    "Portfolio values use the current prices stored in the portfolio session. "
    "This dashboard describes the portfolio and does not provide a buy, sell or hold recommendation."
)

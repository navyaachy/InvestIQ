from __future__ import annotations

import streamlit as st


st.set_page_config(
    page_title="InvestIQ | What-If Analysis",
    page_icon="??",
    layout="wide",
)

st.title("What-If Portfolio Analysis")
st.caption("Explore hypothetical price changes and their effect on your current portfolio.")


holdings = st.session_state.get("portfolio_holdings", [])

valid = []

for row in holdings:
    try:
        ticker = str(row.get("Ticker", "")).strip().upper()
        quantity = float(row.get("Quantity"))
        current_price = float(row.get("Current Price"))

        if ticker and quantity > 0 and current_price > 0:
            valid.append(
                {
                    "Ticker": ticker,
                    "Quantity": quantity,
                    "Current Price": current_price,
                }
            )
    except (TypeError, ValueError):
        continue


if not valid:
    st.info("Add holdings with current prices from the main InvestIQ page first.")
    st.stop()


st.markdown("### Scenario Inputs")

selected_ticker = st.selectbox(
    "Select a holding",
    [row["Ticker"] for row in valid],
)

scenario_change = st.slider(
    "Hypothetical price change",
    min_value=-50,
    max_value=50,
    value=0,
    step=5,
    format="%d%%",
)


selected = next(
    row for row in valid
    if row["Ticker"] == selected_ticker
)


current_total = sum(
    row["Quantity"] * row["Current Price"]
    for row in valid
)

selected_current_value = (
    selected["Quantity"] * selected["Current Price"]
)

scenario_price = selected["Current Price"] * (
    1 + scenario_change / 100
)

scenario_selected_value = (
    selected["Quantity"] * scenario_price
)

portfolio_change = (
    scenario_selected_value - selected_current_value
)

scenario_total = current_total + portfolio_change

portfolio_impact_pct = (
    portfolio_change / current_total * 100
    if current_total
    else 0
)


st.markdown("### Scenario Result")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Current Portfolio Value",
    f"?{current_total:,.0f}",
)

c2.metric(
    "Scenario Portfolio Value",
    f"?{scenario_total:,.0f}",
)

c3.metric(
    "Portfolio Value Change",
    f"?{portfolio_change:,.0f}",
)

c4.metric(
    "Portfolio Impact",
    f"{portfolio_impact_pct:.2f}%",
)


st.markdown("### Selected Holding")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Current Price",
    f"?{selected['Current Price']:,.2f}",
)

c2.metric(
    "Scenario Price",
    f"?{scenario_price:,.2f}",
)

c3.metric(
    "Holding Value Change",
    f"?{portfolio_change:,.0f}",
)


st.markdown("### Portfolio Impact by Holding")

impact_rows = []

for row in valid:

    current_value = row["Quantity"] * row["Current Price"]

    if row["Ticker"] == selected_ticker:
        scenario_value = row["Quantity"] * scenario_price
    else:
        scenario_value = current_value

    impact_rows.append(
        {
            "Ticker": row["Ticker"],
            "Current Value": current_value,
            "Scenario Value": scenario_value,
            "Change": scenario_value - current_value,
        }
    )


for row in impact_rows:
    row["Current Value"] = f"?{row['Current Value']:,.0f}"
    row["Scenario Value"] = f"?{row['Scenario Value']:,.0f}"
    row["Change"] = f"?{row['Change']:,.0f}"


st.dataframe(
    impact_rows,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### What This Means")

st.write(
    f"If **{selected_ticker}** changes by {scenario_change:+.0f}%, "
    f"the portfolio's estimated current value would change by "
    f"?{portfolio_change:,.0f}, assuming all other holdings remain unchanged."
)

st.caption(
    "This is a deterministic what-if calculation, not a price forecast. "
    "It does not estimate the probability that the selected scenario will occur."
)

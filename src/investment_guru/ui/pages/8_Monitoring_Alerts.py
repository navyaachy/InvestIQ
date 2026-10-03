from __future__ import annotations

import streamlit as st


st.set_page_config(
    page_title="InvestIQ | Monitoring & Alerts",
    page_icon="🔔",
    layout="wide",
)

st.title("Monitoring & Alerts")
st.caption(
    "Rule-based portfolio monitoring. Alerts identify conditions in your "
    "current portfolio and do not predict future prices."
)

holdings = st.session_state.get("portfolio_holdings", [])

if not holdings:
    st.info("Add holdings from the main InvestIQ page first.")
    st.stop()


# -----------------------------
# Settings
# -----------------------------

st.markdown("### Alert Settings")

col1, col2, col3 = st.columns(3)

with col1:
    loss_threshold = st.number_input(
        "Loss alert threshold (%)",
        min_value=1.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
    )

with col2:
    gain_threshold = st.number_input(
        "Gain alert threshold (%)",
        min_value=1.0,
        max_value=500.0,
        value=20.0,
        step=1.0,
    )

with col3:
    concentration_threshold = st.number_input(
        "Concentration alert (%)",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=5.0,
    )


# -----------------------------
# Portfolio calculations
# -----------------------------

valid_holdings = []

for row in holdings:

    ticker = str(row.get("Ticker", "")).strip().upper()

    try:
        quantity = float(row.get("Quantity", 0))
        buy_price = float(row.get("Buy Price", 0))
        current_price = float(row.get("Current Price", 0))
    except (TypeError, ValueError):
        continue

    if (
        ticker
        and quantity > 0
        and buy_price > 0
        and current_price > 0
    ):
        current_value = quantity * current_price
        invested_value = quantity * buy_price
        return_pct = (
            (current_value - invested_value)
            / invested_value
            * 100
        )

        valid_holdings.append(
            {
                "Ticker": ticker,
                "Current Value": current_value,
                "Return %": return_pct,
            }
        )


if not valid_holdings:
    st.warning("No valid holdings are available for monitoring.")
    st.stop()


total_value = sum(
    row["Current Value"]
    for row in valid_holdings
)


for row in valid_holdings:
    row["Weight %"] = (
        row["Current Value"] / total_value * 100
        if total_value
        else 0
    )


# -----------------------------
# Alert generation
# -----------------------------

alerts = []

for row in valid_holdings:

    ticker = row["Ticker"]
    return_pct = row["Return %"]
    weight = row["Weight %"]

    if return_pct <= -loss_threshold:
        alerts.append(
            {
                "Type": "Loss threshold",
                "Ticker": ticker,
                "Message": (
                    f"{ticker} is {abs(return_pct):.2f}% below "
                    f"its recorded buy price."
                ),
            }
        )

    if return_pct >= gain_threshold:
        alerts.append(
            {
                "Type": "Gain threshold",
                "Ticker": ticker,
                "Message": (
                    f"{ticker} is {return_pct:.2f}% above "
                    f"its recorded buy price."
                ),
            }
        )

    if weight >= concentration_threshold:
        alerts.append(
            {
                "Type": "Concentration",
                "Ticker": ticker,
                "Message": (
                    f"{ticker} represents {weight:.2f}% of "
                    f"current portfolio value."
                ),
            }
        )


# -----------------------------
# Summary
# -----------------------------

st.markdown("### Monitoring Summary")

summary1, summary2, summary3 = st.columns(3)

with summary1:
    st.metric(
        "Holdings monitored",
        len(valid_holdings),
    )

with summary2:
    st.metric(
        "Portfolio value",
        f"₹{total_value:,.0f}",
    )

with summary3:
    st.metric(
        "Active alerts",
        len(alerts),
    )


# -----------------------------
# Alerts
# -----------------------------

st.markdown("### Current Alerts")

if not alerts:

    st.success(
        "No configured alert conditions are currently triggered."
    )

else:

    for alert in alerts:

        if alert["Type"] == "Loss threshold":
            st.error(
                f"📉 **{alert['Type']} · {alert['Ticker']}**  \n"
                f"{alert['Message']}"
            )

        elif alert["Type"] == "Gain threshold":
            st.success(
                f"📈 **{alert['Type']} · {alert['Ticker']}**  \n"
                f"{alert['Message']}"
            )

        else:
            st.warning(
                f"⚠️ **{alert['Type']} · {alert['Ticker']}**  \n"
                f"{alert['Message']}"
            )


# -----------------------------
# Portfolio monitoring table
# -----------------------------

st.markdown("### Holding Monitoring")

display_rows = []

for row in valid_holdings:

    status = "No alert"

    if row["Return %"] <= -loss_threshold:
        status = "Loss threshold"

    elif row["Return %"] >= gain_threshold:
        status = "Gain threshold"

    elif row["Weight %"] >= concentration_threshold:
        status = "Concentration"

    display_rows.append(
        {
            "Ticker": row["Ticker"],
            "Portfolio Weight %": round(row["Weight %"], 2),
            "Return %": round(row["Return %"], 2),
            "Status": status,
        }
    )

st.dataframe(
    display_rows,
    use_container_width=True,
    hide_index=True,
)


# -----------------------------
# Methodology
# -----------------------------

st.markdown("### How Monitoring Works")

st.write(
    "InvestIQ compares your current portfolio state against the "
    "thresholds you configure above. These rules are descriptive "
    "alerts, not forecasts."
)

st.write(
    "The gain/loss calculation uses the recorded buy price in your "
    "portfolio. Concentration uses each holding's current portfolio value."
)

st.caption(
    "Alerts are evaluated when this page is loaded or refreshed. "
    "Automatic background notifications will be added separately."
)

from __future__ import annotations

import streamlit as st


st.set_page_config(
    page_title="InvestIQ | Investment Goals",
    page_icon="??",
    layout="wide",
)

st.title("Investment Goals")
st.caption("Track progress toward a target amount using your current portfolio value.")


holdings = st.session_state.get("portfolio_holdings", [])

current_value = 0.0

for row in holdings:
    try:
        quantity = float(row.get("Quantity"))
        price = float(row.get("Current Price"))
        if quantity > 0 and price > 0:
            current_value += quantity * price
    except (TypeError, ValueError):
        continue


if current_value <= 0:
    st.info("Add holdings with current prices from the main InvestIQ page first.")
    st.stop()


st.markdown("### Set Your Goal")

c1, c2 = st.columns(2)

with c1:
    target_amount = st.number_input(
        "Target amount (?)",
        min_value=1_000.0,
        value=1_000_000.0,
        step=10_000.0,
    )

with c2:
    years = st.number_input(
        "Time horizon (years)",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
    )


amount_remaining = max(target_amount - current_value, 0)
progress = min(current_value / target_amount * 100, 100)


st.markdown("### Goal Progress")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Current Portfolio", f"?{current_value:,.0f}")
c2.metric("Target Amount", f"?{target_amount:,.0f}")
c3.metric("Amount Remaining", f"?{amount_remaining:,.0f}")
c4.metric("Progress", f"{progress:.2f}%")


st.progress(progress / 100)


st.markdown("### Goal Context")

if current_value >= target_amount:
    st.success("The current portfolio value is already at or above the selected target.")
else:
    st.info(
        f"?{amount_remaining:,.0f} remains between the current portfolio value "
        f"and the selected target."
    )


st.markdown("### Goal Inputs")

monthly_contribution = st.number_input(
    "Optional monthly contribution (?)",
    min_value=0.0,
    value=0.0,
    step=1_000.0,
)

total_future_contributions = monthly_contribution * years * 12

projected_without_returns = current_value + total_future_contributions

c1, c2 = st.columns(2)

c1.metric(
    "Planned Contributions",
    f"?{total_future_contributions:,.0f}",
)

c2.metric(
    "Current Value + Contributions",
    f"?{projected_without_returns:,.0f}",
)


st.markdown("### What This Means")

st.write(
    "This view tracks the gap between your current portfolio value and your "
    "selected target. Planned contributions are shown separately without "
    "assuming a future investment return."
)

st.caption(
    "No future return or market performance is assumed. This is goal-progress "
    "tracking, not a guarantee or investment recommendation."
)

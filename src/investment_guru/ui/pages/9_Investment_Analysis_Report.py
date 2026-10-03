from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests
import streamlit as st
import yfinance as yf


st.set_page_config(
    page_title="InvestIQ | Investment Analysis Report",
    page_icon="📊",
    layout="wide",
)

st.title("Investment Analysis Report")
st.caption(
    "A consolidated, evidence-based summary of your current portfolio. "
    "This report supports research and decision-making and does not provide "
    "buy, sell, or hold recommendations."
)

holdings = st.session_state.get("portfolio_holdings", [])

if not holdings:
    st.info("Add holdings from the main InvestIQ page first.")
    st.stop()


# ============================================================
# Portfolio preparation
# ============================================================

valid = []

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
        invested = quantity * buy_price
        current = quantity * current_price
        pnl = current - invested
        return_pct = pnl / invested * 100 if invested else 0

        valid.append(
            {
                "Ticker": ticker,
                "Quantity": quantity,
                "Buy Price": buy_price,
                "Current Price": current_price,
                "Invested Value": invested,
                "Current Value": current,
                "P&L": pnl,
                "Return %": return_pct,
            }
        )


if not valid:
    st.warning("No valid holdings are available for the report.")
    st.stop()


invested_total = sum(x["Invested Value"] for x in valid)
current_total = sum(x["Current Value"] for x in valid)
pnl_total = current_total - invested_total
return_total = pnl_total / invested_total * 100 if invested_total else 0

for row in valid:
    row["Weight %"] = (
        row["Current Value"] / current_total * 100
        if current_total
        else 0
    )


# ============================================================
# Header
# ============================================================

generated_at = datetime.now().strftime("%d %b %Y, %H:%M")

st.markdown(
    f"**Report generated:** {generated_at}"
)

st.divider()


# ============================================================
# Executive Snapshot
# ============================================================

st.markdown("## 1. Executive Snapshot")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Portfolio Value",
        f"₹{current_total:,.0f}",
    )

with c2:
    st.metric(
        "Invested Value",
        f"₹{invested_total:,.0f}",
    )

with c3:
    st.metric(
        "P&L",
        f"₹{pnl_total:,.0f}",
    )

with c4:
    st.metric(
        "Portfolio Return",
        f"{return_total:.2f}%",
    )


# ============================================================
# Holdings
# ============================================================

st.markdown("## 2. Holdings Overview")

holding_table = []

for row in valid:
    holding_table.append(
        {
            "Ticker": row["Ticker"],
            "Quantity": row["Quantity"],
            "Current Price": round(row["Current Price"], 2),
            "Invested Value": round(row["Invested Value"], 2),
            "Current Value": round(row["Current Value"], 2),
            "P&L": round(row["P&L"], 2),
            "Return %": round(row["Return %"], 2),
            "Portfolio Weight %": round(row["Weight %"], 2),
        }
    )

st.dataframe(
    holding_table,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# Concentration
# ============================================================

largest_weight = max(x["Weight %"] for x in valid)
hhi = sum((x["Weight %"] / 100) ** 2 for x in valid)
effective_holdings = 1 / hhi if hhi else 0

st.markdown("## 3. Portfolio Concentration")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Largest Holding",
        f"{largest_weight:.2f}%",
    )

with c2:
    st.metric(
        "HHI",
        f"{hhi:.3f}",
    )

with c3:
    st.metric(
        "Effective Holdings",
        f"{effective_holdings:.2f}",
    )

if largest_weight >= 50:
    st.warning(
        "The portfolio is highly concentrated in its largest holding."
    )
elif largest_weight >= 30:
    st.info(
        "The largest holding represents a material share of the portfolio."
    )
else:
    st.success(
        "No single holding currently represents 30% or more of portfolio value."
    )


# ============================================================
# Risk
# ============================================================

st.markdown("## 4. Portfolio Risk")

try:

    from src.investment_guru.analytics.portfolio_risk import (
        build_portfolio_risk,
    )

    risk_result = build_portfolio_risk(
        valid,
        benchmark="^NSEI",
        period="1y",
    )

    portfolio_volatility = risk_result.get("portfolio_volatility")
    portfolio_beta = risk_result.get("portfolio_beta")
    concentration = risk_result.get(
        "concentration_level",
        "Unavailable",
    )

    r1, r2, r3 = st.columns(3)

    with r1:
        st.metric(
            "Annualized Volatility",
            f"{portfolio_volatility * 100:.2f}%"
            if portfolio_volatility is not None
            else "Unavailable",
        )

    with r2:
        st.metric(
            "Portfolio Beta",
            f"{portfolio_beta:.2f}"
            if portfolio_beta is not None
            else "Unavailable",
        )

    with r3:
        st.metric(
            "Concentration",
            str(concentration),
        )

    holding_risk = risk_result.get("stock_metrics")

    if holding_risk is not None:

        if hasattr(holding_risk, "to_dict"):
            risk_records = holding_risk.to_dict(
                orient="records"
            )
        elif isinstance(holding_risk, list):
            risk_records = holding_risk
        else:
            risk_records = []

        if risk_records:
            st.dataframe(
                risk_records,
                use_container_width=True,
                hide_index=True,
            )

except Exception as exc:

    st.info(
        f"Portfolio risk metrics were not available for this report: {exc}"
    )


# ============================================================
# Stock Evidence
# ============================================================

st.markdown("## 5. Stock-Level Evidence")

for row in valid:

    ticker = row["Ticker"]

    with st.expander(ticker, expanded=True):

        try:

            info = yf.Ticker(ticker).info

            metrics = {
                "Sector": info.get("sector"),
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
            }

            display = []

            for name, value in metrics.items():

                if value is None:
                    formatted = "Unavailable"

                elif name in {
                    "Revenue Growth",
                    "Earnings Growth",
                    "Profit Margin",
                    "ROE",
                }:
                    formatted = f"{value * 100:.2f}%"

                elif name == "Market Cap":
                    formatted = f"₹{value:,.0f}"

                else:
                    try:
                        formatted = f"{value:.2f}"
                    except (TypeError, ValueError):
                        formatted = str(value)

                display.append(
                    {
                        "Metric": name,
                        "Value": formatted,
                    }
                )

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
            )

        except Exception as exc:

            st.info(
                f"Stock-level data was unavailable for {ticker}: {exc}"
            )


# ============================================================
# Historical Context
# ============================================================

st.markdown("## 6. Historical Context")

st.write(
    "InvestIQ's Historical Analysis reconstructs portfolio behaviour "
    "from current holdings and historical market prices. It does not "
    "represent actual historical transactions or realized returns."
)

try:

    import yfinance as yf
    import pandas as pd

    tickers = [x["Ticker"] for x in valid]

    data = yf.download(
        tickers,
        period="1y",
        auto_adjust=True,
        progress=False,
    )

    if not data.empty:

        if isinstance(data.columns, pd.MultiIndex):

            close = data["Close"]

        else:

            close = data[["Close"]]

            close.columns = tickers

        close = close.dropna(how="all")

        if len(close) >= 2:

            first_values = close.iloc[0]
            last_values = close.iloc[-1]

            performance_rows = []

            for ticker in tickers:

                if (
                    ticker in close.columns
                    and pd.notna(first_values[ticker])
                    and pd.notna(last_values[ticker])
                ):

                    performance = (
                        last_values[ticker]
                        / first_values[ticker]
                        - 1
                    ) * 100

                    performance_rows.append(
                        {
                            "Ticker": ticker,
                            "1Y Price Return %": round(
                                performance,
                                2,
                            ),
                        }
                    )

            st.dataframe(
                performance_rows,
                use_container_width=True,
                hide_index=True,
            )

except Exception:

    st.info(
        "Historical market data was unavailable while generating the report."
    )


# ============================================================
# Monitoring Alerts
# ============================================================

st.markdown("## 7. Monitoring Alerts")

loss_threshold = 10.0
gain_threshold = 20.0
concentration_threshold = 30.0

alerts = []

for row in valid:

    if row["Return %"] <= -loss_threshold:

        alerts.append(
            f"Loss threshold: {row['Ticker']} is "
            f"{abs(row['Return %']):.2f}% below its recorded buy price."
        )

    if row["Return %"] >= gain_threshold:

        alerts.append(
            f"Gain threshold: {row['Ticker']} is "
            f"{row['Return %']:.2f}% above its recorded buy price."
        )

    if row["Weight %"] >= concentration_threshold:

        alerts.append(
            f"Concentration: {row['Ticker']} represents "
            f"{row['Weight %']:.2f}% of current portfolio value."
        )


if alerts:

    for alert in alerts:
        st.warning(alert)

else:

    st.success(
        "No default monitoring thresholds are currently triggered."
    )


# ============================================================
# News
# ============================================================

st.markdown("## 8. Recent News Context")


def fetch_news(company_name: str, ticker: str) -> list[dict]:

    queries = [
        f'"{company_name}" stock',
        f'"{company_name}" India business',
        ticker,
    ]

    articles = []
    seen = set()

    for query in queries:

        url = (
            "https://news.google.com/rss/search?"
            f"q={quote(query)}"
            "&hl=en-IN&gl=IN&ceid=IN:en"
        )

        try:

            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )

            response.raise_for_status()

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):

                title = item.findtext("title")
                link = item.findtext("link")
                pub_date = item.findtext("pubDate")
                source = item.find("source")

                if not title or not link:
                    continue

                key = title.lower().strip()

                if key in seen:
                    continue

                seen.add(key)

                publisher = (
                    source.text
                    if source is not None and source.text
                    else "News publisher"
                )

                articles.append(
                    {
                        "title": title.strip(),
                        "link": link.strip(),
                        "publisher": publisher,
                        "date": pub_date or "",
                    }
                )

                if len(articles) >= 5:
                    return articles

        except Exception:
            continue

    return articles[:5]


company_names = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ICICIBANK.NS": "ICICI Bank",
    "SBIN.NS": "State Bank of India",
    "ITC.NS": "ITC Limited",
    "BHARTIARTL.NS": "Bharti Airtel",
    "LT.NS": "Larsen & Toubro",
    "MARUTI.NS": "Maruti Suzuki",
    "TITAN.NS": "Titan Company",
}

news_count = 0

for row in valid:

    company = company_names.get(
        row["Ticker"],
        row["Ticker"].replace(".NS", "").replace(".BO", ""),
    )

    articles = fetch_news(
        company,
        row["Ticker"],
    )

    if articles:

        st.markdown(f"**{row['Ticker']}**")

        for article in articles:

            st.markdown(
                f"- [{article['title']}]({article['link']})  \n"
                f"  {article['publisher']}"
            )

            news_count += 1


if news_count == 0:

    st.info(
        "No recent news was available while generating the report."
    )


# ============================================================
# Research Considerations
# ============================================================

st.markdown("## 9. Research Considerations")

considerations = []

if largest_weight >= 30:

    considerations.append(
        "Review whether the current portfolio concentration is consistent "
        "with your intended diversification."
    )

if return_total < 0:

    considerations.append(
        "Review the factors contributing to the current negative portfolio "
        "return rather than interpreting the return alone."
    )

if return_total >= 0:

    considerations.append(
        "Review whether current portfolio performance is supported by "
        "fundamental and valuation evidence."
    )

considerations.extend(
    [
        "Review recent company developments alongside financial evidence.",
        "Compare valuation metrics with relevant sector or peer context.",
        "Consider whether the analytical horizon matches the intended "
        "investment horizon.",
        "Review risk, drawdown, and concentration before making portfolio changes.",
    ]
)

for item in considerations:
    st.write(f"• {item}")


# ============================================================
# Methodology
# ============================================================

st.markdown("## 10. Methodology & Limitations")

st.write(
    "InvestIQ combines portfolio holdings, market prices, historical "
    "market behaviour, fundamental and valuation metrics, portfolio risk, "
    "news context, and rule-based monitoring."
)

st.write(
    "Unavailable data is not estimated or silently substituted. Individual "
    "sections may therefore contain unavailable metrics when the underlying "
    "provider does not supply sufficient information."
)

st.write(
    "The report is analytical and descriptive. It does not forecast future "
    "prices, guarantee returns, or provide a buy, sell, or hold recommendation."
)

st.caption(
    "Market and company data are retrieved from external data providers. "
    "News is sourced through Google News RSS. Data availability and timing "
    "depend on those providers."
)


# ============================================================
# Downloadable report
# ============================================================

st.markdown("## 11. Export Report")

report_lines = [
    "# InvestIQ Investment Analysis Report",
    "",
    f"Generated: {generated_at}",
    "",
    "## Executive Snapshot",
    f"- Portfolio Value: ₹{current_total:,.2f}",
    f"- Invested Value: ₹{invested_total:,.2f}",
    f"- P&L: ₹{pnl_total:,.2f}",
    f"- Portfolio Return: {return_total:.2f}%",
    "",
    "## Holdings",
]

for row in valid:

    report_lines.extend(
        [
            f"- {row['Ticker']}: "
            f"{row['Quantity']} units, "
            f"Current Value ₹{row['Current Value']:,.2f}, "
            f"Return {row['Return %']:.2f}%, "
            f"Weight {row['Weight %']:.2f}%",
        ]
    )

report_lines.extend(
    [
        "",
        "## Concentration",
        f"- Largest Holding: {largest_weight:.2f}%",
        f"- HHI: {hhi:.3f}",
        f"- Effective Holdings: {effective_holdings:.2f}",
        "",
        "## Monitoring Alerts",
    ]
)

if alerts:

    report_lines.extend(
        [f"- {alert}" for alert in alerts]
    )

else:

    report_lines.append(
        "- No default monitoring thresholds triggered."
    )

report_lines.extend(
    [
        "",
        "## Methodology",
        "This report is descriptive and evidence-based. "
        "It does not provide buy, sell, or hold recommendations.",
        "",
        "Data availability depends on external providers. "
        "Unavailable metrics are not estimated.",
    ]
)

report_text = "\n".join(report_lines)

st.download_button(
    label="Download Investment Analysis Report",
    data=report_text,
    file_name="InvestIQ_Investment_Analysis_Report.md",
    mime="text/markdown",
)

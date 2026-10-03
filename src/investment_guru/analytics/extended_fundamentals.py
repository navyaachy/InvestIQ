from __future__ import annotations

from typing import Any

import yfinance as yf


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        result = float(value)
        if result != result:
            return None
        return result
    except (TypeError, ValueError):
        return None


def _latest_statement_value(statement, row_names: tuple[str, ...]) -> float | None:
    if statement is None or getattr(statement, "empty", True):
        return None

    for row_name in row_names:
        try:
            if row_name in statement.index:
                row = statement.loc[row_name]
                if hasattr(row, "dropna"):
                    row = row.dropna()
                if len(row) > 0:
                    return _as_float(row.iloc[0])
        except Exception:
            continue

    return None


def _safe_info(ticker: str) -> dict[str, Any]:
    try:
        info = yf.Ticker(ticker).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def enrich_fundamental_data(
    ticker: str,
    fundamentals: dict[str, Any],
) -> dict[str, Any]:
    """
    Add extended fundamental metrics to the existing fundamentals dictionary.

    Existing metrics are preserved. New metrics are populated only when the
    provider supplies enough information to calculate them. Missing values
    remain None and are displayed as N/A by the UI.

    This module does not create scores, forecasts, or buy/sell conclusions.
    """

    ticker = str(ticker).strip().upper()
    enriched = dict(fundamentals or {})
    info = _safe_info(ticker)

    # Direct provider metrics where available.
    direct_fields = {
        "Return on Assets": "returnOnAssets",
        "Operating Margin": "operatingMargins",
        "Gross Margin": "grossMargins",
        "Interest Coverage": "interestCoverage",
        "Dividend Yield": "dividendYield",
        "Dividend Rate": "dividendRate",
        "Payout Ratio": "payoutRatio",
        "Price to Book": "priceToBook",
        "Enterprise Value": "enterpriseValue",
        "EV / EBITDA": "enterpriseToEbitda",
        "Free Cash Flow": "freeCashflow",
        "Operating Cash Flow": "operatingCashflow",
        "Total Debt": "totalDebt",
        "Total Cash": "totalCash",
    }

    for display_name, provider_key in direct_fields.items():
        value = _as_float(info.get(provider_key))
        if value is not None:
            enriched[display_name] = value

    # ROE may already exist in the base provider, but fill it from yfinance
    # when absent.
    if enriched.get("Return on Equity") is None:
        roe = _as_float(info.get("returnOnEquity"))
        if roe is not None:
            enriched["Return on Equity"] = roe

    # Revenue and profit margin can also be useful fallbacks for the extended
    # section if the base provider does not expose them.
    if enriched.get("Revenue") is None:
        revenue = _as_float(info.get("totalRevenue"))
        if revenue is not None:
            enriched["Revenue"] = revenue

    if enriched.get("Profit Margin") is None:
        margin = _as_float(info.get("profitMargins"))
        if margin is not None:
            enriched["Profit Margin"] = margin

    # Free cash flow conversion = FCF / operating cash flow.
    fcf = _as_float(enriched.get("Free Cash Flow"))
    ocf = _as_float(enriched.get("Operating Cash Flow"))
    if fcf is not None and ocf not in (None, 0):
        enriched["FCF Conversion"] = fcf / ocf

    # ROCE = EBIT / capital employed.
    # Capital employed is approximated as total assets - current liabilities.
    # We use the latest annual statement values and leave the metric unavailable
    # if the necessary rows cannot be retrieved.
    try:
        stock = yf.Ticker(ticker)
        income = getattr(stock, "financials", None)
        balance = getattr(stock, "balance_sheet", None)

        ebit = _latest_statement_value(
            income,
            (
                "EBIT",
                "Operating Income",
            ),
        )
        total_assets = _latest_statement_value(
            balance,
            ("Total Assets",),
        )
        current_liabilities = _latest_statement_value(
            balance,
            ("Current Liabilities",),
        )

        if ebit is not None and total_assets is not None and current_liabilities is not None:
            capital_employed = total_assets - current_liabilities
            if capital_employed > 0:
                enriched["ROCE"] = ebit / capital_employed

        # Interest coverage fallback when provider does not expose it.
        if enriched.get("Interest Coverage") is None and ebit is not None:
            interest_expense = _latest_statement_value(
                income,
                (
                    "Interest Expense Non Operating",
                    "Interest Expense",
                    "Interest Expense Non Operating",
                ),
            )
            if interest_expense is not None and interest_expense != 0:
                enriched["Interest Coverage"] = ebit / abs(interest_expense)

        # Operating and net margins can be reconstructed from statements.
        if enriched.get("Operating Margin") is None and ebit is not None:
            revenue = _latest_statement_value(
                income,
                (
                    "Total Revenue",
                    "Operating Revenue",
                ),
            )
            if revenue not in (None, 0):
                enriched["Operating Margin"] = ebit / revenue

    except Exception:
        pass

    # Keep explicit metadata so the UI can distinguish provider-derived
    # extended metrics from the existing scoring framework.
    enriched["Extended Fundamentals Source"] = "Yahoo Finance via yfinance"
    enriched["Extended Fundamentals Status"] = "Available"

    return enriched

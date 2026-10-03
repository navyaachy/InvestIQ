from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        number = float(value)
        if number != number:
            return None
        return number
    except (TypeError, ValueError):
        return None


def calculate_holding_values(
    ticker: str,
    quantity: float,
    buy_price: float,
    current_price: float,
) -> dict[str, Any]:
    invested_value = quantity * buy_price
    current_value = quantity * current_price
    pnl = current_value - invested_value
    return_pct = (pnl / invested_value * 100) if invested_value else None

    return {
        "Ticker": ticker.strip().upper(),
        "Quantity": quantity,
        "Buy Price": buy_price,
        "Current Price": current_price,
        "Invested Value": invested_value,
        "Current Value": current_value,
        "P&L": pnl,
        "Return %": return_pct,
    }


def calculate_portfolio_summary(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    valid = []
    for holding in holdings:
        quantity = _to_float(holding.get("Quantity"))
        buy_price = _to_float(holding.get("Buy Price"))
        current_price = _to_float(holding.get("Current Price"))
        ticker = str(holding.get("Ticker", "")).strip().upper()

        if not ticker or quantity is None or buy_price is None or current_price is None:
            continue
        if quantity <= 0 or buy_price <= 0 or current_price <= 0:
            continue

        valid.append(
            calculate_holding_values(
                ticker=ticker,
                quantity=quantity,
                buy_price=buy_price,
                current_price=current_price,
            )
        )

    invested_total = sum(item["Invested Value"] for item in valid)
    current_total = sum(item["Current Value"] for item in valid)
    pnl_total = current_total - invested_total
    return_pct = (pnl_total / invested_total * 100) if invested_total else None

    for item in valid:
        item["Weight %"] = (
            item["Current Value"] / current_total * 100
            if current_total
            else None
        )

    return {
        "holdings": valid,
        "holding_count": len(valid),
        "invested_value": invested_total,
        "current_value": current_total,
        "pnl": pnl_total,
        "return_pct": return_pct,
    }


def refresh_holding_prices(holdings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Refresh prices without estimating or silently substituting values."""
    try:
        from src.investment_guru.data.providers.portfolio_prices import get_current_price
    except ImportError:
        return holdings, ["Portfolio price provider could not be imported."]

    refreshed = []
    errors = []

    for holding in holdings:
        row = dict(holding)
        ticker = str(row.get("Ticker", "")).strip().upper()
        if not ticker:
            refreshed.append(row)
            continue

        try:
            result = get_current_price(ticker)
            price = result.get("current_price") if isinstance(result, dict) else None
            status = result.get("status") if isinstance(result, dict) else None

            if price is not None:
                row["Current Price"] = float(price)
                row["Price Source"] = result.get("source", "Yahoo Finance")
                row["Price Status"] = status or "Available"
                row["Price Retrieval Time"] = result.get("retrieved_at")
            else:
                errors.append(f"{ticker}: current price unavailable and was not estimated.")
        except Exception as exc:
            errors.append(f"{ticker}: price retrieval failed ({exc}).")

        refreshed.append(row)

    return refreshed, errors


from functools import lru_cache


@lru_cache(maxsize=128)
def get_holding_sector(ticker: str) -> dict[str, Any]:
    """Return the provider-reported sector for a ticker."""
    ticker = str(ticker or "").strip().upper()
    if not ticker:
        return {"ticker": ticker, "sector": None, "status": "Unavailable", "message": "Ticker is empty."}

    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        sector = info.get("sector")
        if sector:
            return {
                "ticker": ticker,
                "sector": str(sector),
                "status": "Available",
                "message": "Sector retrieved successfully.",
            }
        return {
            "ticker": ticker,
            "sector": None,
            "status": "Unavailable",
            "message": "Sector was not reported by the provider.",
        }
    except Exception as exc:
        return {
            "ticker": ticker,
            "sector": None,
            "status": "Unavailable",
            "message": f"Sector retrieval failed: {exc}",
        }


def calculate_sector_exposure(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate current portfolio value by provider-reported sector."""
    sector_totals: dict[str, dict[str, Any]] = {}
    unavailable: list[dict[str, str]] = []
    covered_value = 0.0

    for holding in holdings:
        ticker = str(holding.get("Ticker", "")).strip().upper()
        current_value = _to_float(holding.get("Current Value")) or 0.0
        if not ticker or current_value <= 0:
            continue

        sector_result = get_holding_sector(ticker)
        sector = sector_result.get("sector")
        if not sector:
            unavailable.append({
                "Ticker": ticker,
                "Reason": sector_result.get("message", "Sector unavailable."),
            })
            continue

        covered_value += current_value
        if sector not in sector_totals:
            sector_totals[sector] = {
                "Sector": sector,
                "Current Value": 0.0,
                "Holdings": [],
                "Holding Count": 0,
            }

        sector_totals[sector]["Current Value"] += current_value
        sector_totals[sector]["Holdings"].append(ticker)
        sector_totals[sector]["Holding Count"] += 1

    total_current_value = sum(
        _to_float(item.get("Current Value")) or 0.0
        for item in holdings
    )

    sectors = []
    for item in sector_totals.values():
        weight = (
            item["Current Value"] / total_current_value * 100
            if total_current_value
            else None
        )
        item["Weight %"] = weight
        item["Holdings"] = ", ".join(item["Holdings"])
        sectors.append(item)

    sectors.sort(key=lambda item: item["Current Value"], reverse=True)

    return {
        "sectors": sectors,
        "sector_count": len(sectors),
        "covered_value": covered_value,
        "unavailable_holdings": unavailable,
    }

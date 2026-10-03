from __future__ import annotations

from typing import Any

import yfinance as yf


def _safe_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    try:
        if value is None:
            return None

        number = float(value)

        if number != number:
            return None

        return number

    except (TypeError, ValueError):
        return None


def _get_info(ticker: str) -> dict[str, Any]:
    """Retrieve Yahoo Finance information safely."""

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if isinstance(info, dict):
            return info

    except Exception:
        pass

    return {}


def _calculate_earnings_yield(
    trailing_pe: float | None,
) -> float | None:
    """
    Earnings Yield = 1 / P/E * 100.

    Not meaningful when P/E is zero, negative,
    or unavailable.
    """

    if (
        trailing_pe is None
        or trailing_pe <= 0
    ):
        return None

    return (1 / trailing_pe) * 100


def _calculate_fcf_yield(
    free_cash_flow: float | None,
    market_cap: float | None,
) -> float | None:
    """
    FCF Yield = Free Cash Flow / Market Cap * 100.
    """

    if (
        free_cash_flow is None
        or market_cap is None
        or market_cap <= 0
    ):
        return None

    return (
        free_cash_flow
        / market_cap
    ) * 100


def _relative_to_peer(
    value: float | None,
    peer_median: float | None,
) -> dict[str, Any]:
    """
    Compare a metric with a supplied peer median.

    This function does not decide whether the stock
    is attractive. It only describes the numerical
    relationship.
    """

    if value is None or peer_median is None:
        return {
            "value": value,
            "peer_median": peer_median,
            "difference_pct": None,
            "relationship": "Unavailable",
        }

    if peer_median == 0:
        return {
            "value": value,
            "peer_median": peer_median,
            "difference_pct": None,
            "relationship": "Unavailable",
        }

    difference_pct = (
        (value - peer_median)
        / abs(peer_median)
    ) * 100

    if difference_pct > 10:
        relationship = "Above peer median"

    elif difference_pct < -10:
        relationship = "Below peer median"

    else:
        relationship = "Near peer median"

    return {
        "value": round(value, 2),
        "peer_median": round(peer_median, 2),
        "difference_pct": round(
            difference_pct,
            2,
        ),
        "relationship": relationship,
    }


def build_valuation_context(
    ticker: str,
    peer_medians: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a valuation context for a stock.

    Included metrics:

        Trailing P/E
        Forward P/E
        P/B
        EV/EBITDA
        Earnings Yield
        FCF Yield
        Market Cap
        Enterprise Value

    Optional peer-relative comparison can be supplied
    through peer_medians.

    Example:

        {
            "Trailing P/E": 22.4,
            "Forward P/E": 19.8,
            "P/B": 3.1,
            "EV/EBITDA": 15.2,
        }

    Historical valuation is NOT fabricated. Yahoo Finance
    does not provide a reliable historical valuation series
    through this interface, so historical values remain
    unavailable unless a dedicated historical source is
    added later.
    """

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError(
            "Ticker cannot be empty."
        )

    info = _get_info(ticker)

    if not info:
        return {
            "ticker": ticker,
            "status": "UNAVAILABLE",
            "message": (
                "Valuation information could not "
                "be retrieved from Yahoo Finance."
            ),
            "metrics": {},
            "peer_comparison": {},
            "historical_context": {
                "status": "Unavailable",
                "message": (
                    "Historical valuation data is not "
                    "available from the current provider."
                ),
            },
        }

    trailing_pe = _safe_float(
        info.get("trailingPE")
    )

    forward_pe = _safe_float(
        info.get("forwardPE")
    )

    price_to_book = _safe_float(
        info.get("priceToBook")
    )

    ev_to_ebitda = _safe_float(
        info.get("enterpriseToEbitda")
    )

    market_cap = _safe_float(
        info.get("marketCap")
    )

    enterprise_value = _safe_float(
        info.get("enterpriseValue")
    )

    free_cash_flow = _safe_float(
        info.get("freeCashflow")
    )

    earnings_yield = (
        _calculate_earnings_yield(
            trailing_pe
        )
    )

    fcf_yield = _calculate_fcf_yield(
        free_cash_flow,
        market_cap,
    )

    metrics = {
        "Trailing P/E": trailing_pe,
        "Forward P/E": forward_pe,
        "P/B": price_to_book,
        "EV/EBITDA": ev_to_ebitda,
        "Earnings Yield": earnings_yield,
        "FCF Yield": fcf_yield,
        "Market Cap": market_cap,
        "Enterprise Value": enterprise_value,
    }

    peer_medians = (
        peer_medians
        if isinstance(peer_medians, dict)
        else {}
    )

    peer_comparison = {}

    for metric_name, value in metrics.items():

        if metric_name in peer_medians:

            peer_comparison[
                metric_name
            ] = _relative_to_peer(
                value=value,
                peer_median=_safe_float(
                    peer_medians[
                        metric_name
                    ]
                ),
            )

    available_metrics = sum(
        value is not None
        for value in metrics.values()
    )

    return {
        "ticker": ticker,
        "status": "OK",
        "message": (
            "Current valuation context "
            "retrieved successfully."
        ),
        "available_metrics": available_metrics,
        "total_metrics": len(metrics),
        "metrics": metrics,
        "peer_comparison": peer_comparison,
        "historical_context": {
            "status": "Unavailable",
            "message": (
                "Historical valuation time-series "
                "data is not available from the "
                "current provider. No historical "
                "valuation values have been estimated."
            ),
        },
    }
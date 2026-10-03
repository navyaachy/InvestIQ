from __future__ import annotations

from functools import lru_cache
from statistics import median
from typing import Any

import yfinance as yf


# Curated liquid Indian reference sets.
# These are deliberately treated as reference peers,
# not as an exhaustive sector universe.
SECTOR_REFERENCE_PEERS: dict[str, list[str]] = {
    "Technology": [
        "TCS.NS",
        "INFY.NS",
        "HCLTECH.NS",
        "WIPRO.NS",
        "TECHM.NS",
    ],
    "Financial Services": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "KOTAKBANK.NS",
        "AXISBANK.NS",
        "SBIN.NS",
    ],
    "Consumer Cyclical": [
        "MARUTI.NS",
        "TITAN.NS",
        "TRENT.NS",
        "DMART.NS",
        "ASIANPAINT.NS",
    ],
    "Consumer Defensive": [
        "HINDUNILVR.NS",
        "ITC.NS",
        "NESTLEIND.NS",
        "BRITANNIA.NS",
        "DABUR.NS",
    ],
    "Healthcare": [
        "SUNPHARMA.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "DIVISLAB.NS",
        "APOLLOHOSP.NS",
    ],
    "Energy": [
        "RELIANCE.NS",
        "ONGC.NS",
        "NTPC.NS",
        "POWERGRID.NS",
        "COALINDIA.NS",
    ],
    "Industrials": [
        "LT.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "BEL.NS",
        "HAL.NS",
    ],
    "Basic Materials": [
        "TATASTEEL.NS",
        "JSWSTEEL.NS",
        "HINDALCO.NS",
        "ULTRACEMCO.NS",
        "GRASIM.NS",
    ],
    "Utilities": [
        "NTPC.NS",
        "POWERGRID.NS",
        "TATAPOWER.NS",
        "ADANIGREEN.NS",
        "ADANIPOWER.NS",
    ],
    "Real Estate": [
        "DLF.NS",
        "GODREJPROP.NS",
        "LODHA.NS",
        "OBEROIRLTY.NS",
        "PRESTIGE.NS",
    ],
    "Communication Services": [
        "BHARTIARTL.NS",
        "IDEA.NS",
    ],
}


# Metric definitions.
#
# yfinance returns several percentage metrics as decimals:
#
#     0.0618 = 6.18%
#
# InvestIQ's fundamental scoring layer represents some of these
# metrics as percentages:
#
#     6.18 = 6.18%
#
# The scale field makes the conversion explicit and prevents
# target/peer unit mismatches.
METRIC_SPECS: dict[str, dict[str, Any]] = {
    "P/E Ratio": {
        "info_key": "trailingPE",
        "scale": 1.0,
    },
    "Forward P/E": {
        "info_key": "forwardPE",
        "scale": 1.0,
    },
    "Return on Equity": {
        "info_key": "returnOnEquity",
        "scale": 100.0,
    },
    "Debt to Equity": {
        "info_key": "debtToEquity",
        "scale": 1.0,
    },
    "Profit Margin": {
        "info_key": "profitMargins",
        "scale": 100.0,
    },
    "Revenue Growth": {
        "info_key": "revenueGrowth",
        "scale": 1.0,
    },
}


def _normalise_ticker(ticker: str) -> str:
    value = str(ticker or "").strip().upper()

    if not value:
        return value

    if "." not in value and not value.startswith("^"):
        return f"{value}.NS"

    return value


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None

        number = float(value)

        if number != number:
            return None

        return number

    except (TypeError, ValueError):
        return None


def _extract_info(ticker: str) -> dict[str, Any]:
    try:
        return dict(
            yf.Ticker(ticker).info or {}
        )

    except Exception:
        return {}


def _scale_metric(
    value: Any,
    scale: float,
) -> float | None:
    number = _safe_float(value)

    if number is None:
        return None

    return number * scale


@lru_cache(maxsize=64)
def _cached_peer_snapshot(
    peer_tickers: tuple[str, ...],
) -> list[dict[str, Any]]:

    rows: list[dict[str, Any]] = []

    for peer in peer_tickers:

        info = _extract_info(peer)

        if not info:
            continue

        row: dict[str, Any] = {
            "ticker": peer,
            "company": (
                info.get("longName")
                or info.get("shortName")
                or peer
            ),
        }

        for label, spec in METRIC_SPECS.items():

            raw_value = info.get(
                spec["info_key"]
            )

            row[label] = _scale_metric(
                raw_value,
                spec["scale"],
            )

        rows.append(row)

    return rows


def _percentile_rank(
    value: float | None,
    peer_values: list[float],
) -> float | None:

    if value is None or not peer_values:
        return None

    less_or_equal = sum(
        item <= value
        for item in peer_values
    )

    return round(
        (less_or_equal / len(peer_values)) * 100,
        1,
    )


def _relative_text(
    value: float | None,
    peer_median: float | None,
) -> str:

    if value is None or peer_median is None:
        return "Not available"

    if peer_median == 0:
        return "Median is zero"

    difference = (
        (value - peer_median)
        / abs(peer_median)
    ) * 100

    if abs(difference) < 5:
        return "Near peer median"

    if difference > 0:
        return (
            f"{difference:.1f}% "
            "above peer median"
        )

    return (
        f"{abs(difference):.1f}% "
        "below peer median"
    )


def build_peer_context(
    ticker: str,
    fundamentals: dict[str, Any],
) -> dict[str, Any]:
    """Build transparent sector/reference-peer context.

    The peer set is curated and finite. The function never presents it as
    the full sector universe and never turns relative metrics into a buy/sell
    conclusion.

    Percentage-based metrics are normalised so target and peer values use
    the same units before comparison.
    """

    target_ticker = _normalise_ticker(
        ticker
    )

    sector = fundamentals.get(
        "Sector"
    )

    industry = fundamentals.get(
        "Industry"
    )

    peers = list(
        SECTOR_REFERENCE_PEERS.get(
            str(sector),
            [],
        )
    )

    peers = [
        peer
        for peer in peers
        if _normalise_ticker(peer)
        != target_ticker
    ]

    if not peers:
        return {
            "available": False,
            "ticker": target_ticker,
            "sector": sector,
            "industry": industry,
            "reference_type": (
                "Curated sector reference set"
            ),
            "peer_tickers": [],
            "peer_rows": [],
            "metrics": {},
            "message": (
                "No curated reference set is "
                "currently available for this sector."
            ),
        }

    peer_rows = _cached_peer_snapshot(
        tuple(peers)
    )

    metrics: dict[str, Any] = {}

    fundamental_key_map = {
        "P/E Ratio": "P/E Ratio",
        "Forward P/E": "Forward P/E",
        "Return on Equity": "Return on Equity",
        "Debt to Equity": "Debt to Equity",
        "Profit Margin": "Profit Margin",
        "Revenue Growth": "Revenue Growth",
    }

    for label, fundamentals_key in (
        fundamental_key_map.items()
    ):

        target_value = _safe_float(
            fundamentals.get(
                fundamentals_key
            )
        )

        peer_values = [
            row[label]
            for row in peer_rows
            if row.get(label) is not None
        ]

        peer_median = (
            median(peer_values)
            if peer_values
            else None
        )

        metrics[label] = {
            "target": target_value,
            "peer_median": (
                round(
                    peer_median,
                    4,
                )
                if peer_median is not None
                else None
            ),
            "peer_count": len(
                peer_values
            ),
            "percentile": _percentile_rank(
                target_value,
                peer_values,
            ),
            "relative": _relative_text(
                target_value,
                peer_median,
            ),
        }

    return {
        "available": bool(
            peer_rows
        ),
        "ticker": target_ticker,
        "sector": sector,
        "industry": industry,
        "reference_type": (
            "Curated sector reference set"
        ),
        "peer_tickers": [
            row["ticker"]
            for row in peer_rows
        ],
        "peer_rows": peer_rows,
        "metrics": metrics,
        "message": (
            "Relative context is based on "
            "a curated reference set, not "
            "the full sector universe. "
            "It is descriptive and not a "
            "valuation verdict."
        ),
    }
from __future__ import annotations

from typing import Any


def classify_stock_horizon(
    market_behaviour: float | None,
    fundamentals: float | None,
    growth: float | None,
    valuation: float | None,
) -> dict[str, Any]:
    """
    Classify a stock's analytical horizon using the evidence
    already produced by InvestIQ.

    Short-term evidence:
        Market Behaviour

    Longer-term evidence:
        Fundamentals
        Growth
        Valuation

    Risk is intentionally excluded because it measures
    risk quality rather than investment horizon.
    """

    long_term_components = {
        "fundamentals": fundamentals,
        "growth": growth,
        "valuation": valuation,
    }

    available_long_term = [
        value
        for value in long_term_components.values()
        if value is not None
    ]

    long_term_score = None

    if available_long_term:
        long_term_score = (
            sum(available_long_term)
            / len(available_long_term)
        )

    short_term_score = market_behaviour

    # Not enough evidence to classify the horizon.
    if (
        short_term_score is None
        and long_term_score is None
    ):
        return {
            "horizon": None,
            "confidence": "Very limited",
            "short_term_score": None,
            "long_term_score": None,
            "reason": (
                "Insufficient market behaviour and "
                "long-term evidence."
            ),
            "components_available": 0,
        }

    # If only short-term evidence exists.
    if (
        short_term_score is not None
        and long_term_score is None
    ):
        return {
            "horizon": "short-term",
            "confidence": "Limited",
            "short_term_score": round(short_term_score, 2),
            "long_term_score": None,
            "reason": (
                "Only market behaviour evidence is "
                "currently available."
            ),
            "components_available": 1,
        }

    # If only long-term evidence exists.
    if (
        short_term_score is None
        and long_term_score is not None
    ):
        return {
            "horizon": "long-term",
            "confidence": "Moderate",
            "short_term_score": None,
            "long_term_score": round(long_term_score, 2),
            "reason": (
                "Fundamental, growth, and/or valuation "
                "evidence is available, while market "
                "behaviour evidence is unavailable."
            ),
            "components_available": len(available_long_term),
        }

    # Both types of evidence are available.

    # Strong short-term evidence with weaker
    # longer-term evidence.
    if (
        short_term_score >= 65
        and long_term_score < 60
    ):
        horizon = "short-term"

        reason = (
            "Market behaviour currently provides stronger "
            "support than the available longer-term evidence."
        )

    # Stronger longer-term evidence with weaker
    # short-term evidence.
    elif (
        long_term_score >= 65
        and short_term_score < 60
    ):
        horizon = "long-term"

        reason = (
            "Fundamental, growth, and valuation evidence "
            "provides stronger longer-term support than "
            "current market behaviour."
        )

    # Otherwise the evidence is mixed.
    else:
        horizon = "medium-term"

        reason = (
            "Short-term market behaviour and longer-term "
            "fundamental evidence are relatively mixed."
        )

    total_components = (
        1 + len(available_long_term)
    )

    if total_components >= 4:
        confidence = "High"

    elif total_components >= 3:
        confidence = "Moderate"

    else:
        confidence = "Limited"

    return {
        "horizon": horizon,
        "confidence": confidence,
        "short_term_score": round(
            short_term_score,
            2,
        ),
        "long_term_score": round(
            long_term_score,
            2,
        ),
        "reason": reason,
        "components_available": total_components,
    }
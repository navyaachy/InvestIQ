from __future__ import annotations

from typing import Any


def _score_lower_is_better(
    value: float | None,
    good: float,
    expensive: float,
) -> float | None:
    """
    Score a valuation metric where a lower value is generally
    more attractive.

    The score is deliberately transparent and bounded between
    0 and 100.
    """

    if value is None:
        return None

    if value <= good:
        return 100.0

    if value >= expensive:
        return 0.0

    score = 100 * (
        (expensive - value)
        / (expensive - good)
    )

    return round(
        max(0.0, min(100.0, score)),
        2,
    )


def calculate_valuation_scores(
    fundamentals: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate an explainable valuation assessment.

    Current inputs:
    - Trailing P/E
    - Forward P/E

    Missing metrics are excluded rather than treated as zero.
    """

    pe_ratio = fundamentals.get(
        "P/E Ratio"
    )

    forward_pe = fundamentals.get(
        "Forward P/E"
    )

    pe_score = _score_lower_is_better(
        pe_ratio,
        good=15.0,
        expensive=35.0,
    )

    forward_pe_score = _score_lower_is_better(
        forward_pe,
        good=12.0,
        expensive=30.0,
    )

    available_scores = []

    if pe_score is not None:
        available_scores.append(
            pe_score
        )

    if forward_pe_score is not None:
        available_scores.append(
            forward_pe_score
        )

    if available_scores:

        overall_score = sum(
            available_scores
        ) / len(available_scores)

    else:

        overall_score = None

    metric_count = len(
        available_scores
    )

    coverage = (
        metric_count / 2 * 100
    )

    if overall_score is None:

        assessment = (
            "Valuation unavailable"
        )

    elif overall_score >= 70:

        assessment = (
            "Relatively stronger valuation evidence"
        )

    elif overall_score >= 45:

        assessment = (
            "Moderate valuation"
        )

    else:

        assessment = (
            "Relatively expensive valuation"
        )

    return {
        "overall_score": (
            round(overall_score, 2)
            if overall_score is not None
            else None
        ),

        "coverage": round(
            coverage,
            2,
        ),

        "assessment": assessment,

        "components": {
            "trailing_pe": pe_score,
            "forward_pe": forward_pe_score,
        },

        "raw_metrics": {
            "pe_ratio": pe_ratio,
            "forward_pe": forward_pe,
        },
    }

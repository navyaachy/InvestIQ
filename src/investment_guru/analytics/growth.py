from __future__ import annotations

from typing import Any


def _score_growth(value: float | None) -> float | None:
    """
    Score a growth metric on a 0-100 scale.

    The thresholds are transparent heuristics:
    <= 0%   -> 0
    0-5%    -> 40
    5-10%   -> 60
    10-20%  -> 80
    >= 20%  -> 100
    """

    if value is None:
        return None

    value = value * 100

    if value <= 0:
        return 0.0

    if value >= 20:
        return 100.0

    if value >= 10:
        return round(80 + ((value - 10) / 10) * 20, 2)

    if value >= 5:
        return round(60 + ((value - 5) / 5) * 20, 2)

    return round(40 + (value / 5) * 20, 2)


def _build_growth_assessment(
    revenue_growth: float | None,
    earnings_growth: float | None,
    overall_score: float | None,
) -> str:
    """
    Build a human-readable interpretation of the growth evidence.

    This explains the relationship between revenue growth,
    earnings growth, and the overall growth score.
    """

    if overall_score is None:
        return "Growth unavailable"

    revenue_available = revenue_growth is not None
    earnings_available = earnings_growth is not None

    if revenue_available and earnings_available:

        revenue_pct = revenue_growth * 100
        earnings_pct = earnings_growth * 100

        if revenue_pct > 0 and earnings_pct < 0:
            return (
                "Mixed growth profile: strong revenue growth "
                "is offset by negative earnings growth."
            )

        if revenue_pct < 0 and earnings_pct > 0:
            return (
                "Mixed growth profile: positive earnings growth "
                "is offset by declining revenue growth."
            )

        if revenue_pct > 0 and earnings_pct > 0:
            if overall_score >= 75:
                return (
                    "Strong growth profile: both revenue and "
                    "earnings growth are positive."
                )

            if overall_score >= 50:
                return (
                    "Moderate growth profile: both revenue and "
                    "earnings growth are positive but differ in strength."
                )

            return (
                "Limited growth profile: revenue and earnings "
                "growth are positive but remain relatively modest."
            )

        if revenue_pct <= 0 and earnings_pct <= 0:
            return (
                "Weak growth profile: both revenue and earnings "
                "growth are currently non-positive."
            )

    if revenue_available:
        if revenue_growth > 0:
            return (
                f"Revenue growth is positive at "
                f"{revenue_growth * 100:.1f}%, while earnings growth "
                "evidence is unavailable."
            )

        return (
            f"Revenue growth is non-positive at "
            f"{revenue_growth * 100:.1f}%, while earnings growth "
            "evidence is unavailable."
        )

    if earnings_available:
        if earnings_growth > 0:
            return (
                f"Earnings growth is positive at "
                f"{earnings_growth * 100:.1f}%, while revenue growth "
                "evidence is unavailable."
            )

        return (
            f"Earnings growth is non-positive at "
            f"{earnings_growth * 100:.1f}%, while revenue growth "
            "evidence is unavailable."
        )

    return "Growth evidence is unavailable."


def calculate_growth_scores(
    fundamentals: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate an explainable growth score using available growth metrics.
    """

    revenue_growth = fundamentals.get("Revenue Growth")
    earnings_growth = fundamentals.get("Earnings Growth")

    revenue_score = _score_growth(revenue_growth)
    earnings_score = _score_growth(earnings_growth)

    available_scores = []

    if revenue_score is not None:
        available_scores.append(revenue_score)

    if earnings_score is not None:
        available_scores.append(earnings_score)

    if available_scores:
        overall_score = sum(available_scores) / len(available_scores)
    else:
        overall_score = None

    metric_count = len(available_scores)
    coverage = (metric_count / 2) * 100

    assessment = _build_growth_assessment(
        revenue_growth=revenue_growth,
        earnings_growth=earnings_growth,
        overall_score=overall_score,
    )

    return {
        "overall_score": (
            round(overall_score, 2)
            if overall_score is not None
            else None
        ),
        "coverage": round(coverage, 2),
        "assessment": assessment,
        "components": {
            "revenue_growth": revenue_score,
            "earnings_growth": earnings_score,
        },
        "raw_metrics": {
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
        },
    }
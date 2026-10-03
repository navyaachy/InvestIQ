from __future__ import annotations


def score_total_return(total_return: float | None) -> float | None:
    """Score historical total return on a 0-100 scale."""

    if total_return is None:
        return None

    if total_return >= 20:
        return 100
    if total_return >= 10:
        return 80
    if total_return >= 0:
        return 60
    if total_return >= -10:
        return 40
    if total_return >= -20:
        return 20

    return 0


def score_sharpe_ratio(sharpe: float | None) -> float | None:
    """Score risk-adjusted historical performance."""

    if sharpe is None:
        return None

    if sharpe >= 1.5:
        return 100
    if sharpe >= 1.0:
        return 80
    if sharpe >= 0.5:
        return 65
    if sharpe >= 0:
        return 50
    if sharpe >= -0.5:
        return 30

    return 10


def score_volatility(volatility: float | None) -> float | None:
    """Score annualised volatility. Lower volatility receives a higher score."""

    if volatility is None:
        return None

    if volatility <= 0.10:
        return 100
    if volatility <= 0.15:
        return 80
    if volatility <= 0.20:
        return 60
    if volatility <= 0.30:
        return 40
    if volatility <= 0.40:
        return 20

    return 0


def score_max_drawdown(drawdown: float | None) -> float | None:
    """Score maximum drawdown. Smaller losses receive a higher score."""

    if drawdown is None:
        return None

    drawdown = abs(drawdown)

    if drawdown <= 0.10:
        return 100
    if drawdown <= 0.20:
        return 80
    if drawdown <= 0.30:
        return 60
    if drawdown <= 0.40:
        return 40
    if drawdown <= 0.50:
        return 20

    return 0


def calculate_weighted_score(
    scores: dict[str, float | None],
    weights: dict[str, float],
) -> float | None:
    """Calculate a weighted score using only available factors."""

    available = {
        name: score
        for name, score in scores.items()
        if score is not None and name in weights
    }

    if not available:
        return None

    total_weight = sum(weights[name] for name in available)

    if total_weight == 0:
        return None

    weighted_sum = sum(
        available[name] * weights[name]
        for name in available
    )

    return weighted_sum / total_weight
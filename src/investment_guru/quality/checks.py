from __future__ import annotations

import pandas as pd

from src.investment_guru.domain.models import QualityReport, QualityStatus


def check_price_quality(
    price_series,
    min_history_days: int = 20,
) -> QualityReport:
    """Run basic quality checks on a price series."""

    issues: list[str] = []

    data = price_series.data.copy()

    if data.empty:
        return QualityReport(
            ticker=price_series.ticker,
            status=QualityStatus.UNAVAILABLE,
            issues=["No price data available."],
        )

    # Check minimum history
    if len(data) < min_history_days:
        issues.append(
            f"Insufficient trading history: "
            f"{len(data)} observations available; "
            f"{min_history_days} expected."
        )

    # Check required columns
    required_columns = {
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    }

    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        issues.append(
            f"Missing columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    # Check missing values
    available_required_columns = (
        required_columns & set(data.columns)
    )

    missing_values = int(
        data[list(available_required_columns)]
        .isna()
        .sum()
        .sum()
    )

    if missing_values > 0:
        issues.append(
            f"Missing values detected: {missing_values}"
        )

    # Check zero-volume days
    #
    # A small number of zero-volume observations can occur
    # in downloaded market datasets and should not by itself
    # make an otherwise usable dataset low-confidence.
    if "Volume" in data.columns:
        zero_volume = int(
            (data["Volume"] == 0).sum()
        )

        zero_volume_threshold = max(
            5,
            round(len(data) * 0.02),
        )

        if zero_volume > zero_volume_threshold:
            issues.append(
                f"Excessive zero-volume trading days detected: "
                f"{zero_volume}"
            )

    # Check extreme price jumps
    if "Close" in data.columns and len(data) > 1:
        returns = (
            data["Close"]
            .pct_change()
            .dropna()
        )

        extreme_moves = int(
            (returns.abs() > 0.20).sum()
        )

        if extreme_moves > 0:
            issues.append(
                "Extreme single-day price moves "
                f"(>20%): {extreme_moves}"
            )

    # Determine overall status
    if missing_columns or data.empty:
        status = QualityStatus.UNAVAILABLE

    elif issues:
        status = QualityStatus.LOW_CONFIDENCE

    else:
        status = QualityStatus.OK

    return QualityReport(
        ticker=price_series.ticker,
        status=status,
        issues=issues,
    )
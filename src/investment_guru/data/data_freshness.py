
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def classify_data_freshness(
    retrieved_at: str | None,
    market: str = "NSE",
) -> dict[str, object]:
    """
    Classify market-data freshness without treating exchange-closed
    periods as stale data.
    """

    if not retrieved_at:
        return {
            "status": "Unavailable",
            "label": "?? Unavailable",
            "age_minutes": None,
            "message": "No retrieval timestamp is available.",
        }

    try:
        retrieved = datetime.fromisoformat(
            str(retrieved_at).replace("Z", "+00:00")
        )

        if retrieved.tzinfo is None:
            retrieved = retrieved.replace(
                tzinfo=ZoneInfo("UTC")
            )

        now = datetime.now(retrieved.tzinfo)

        age_minutes = max(
            0.0,
            (now - retrieved).total_seconds() / 60,
        )

    except Exception:
        return {
            "status": "Unavailable",
            "label": "?? Unavailable",
            "age_minutes": None,
            "message": "Retrieval timestamp could not be interpreted.",
        }

    local_time = retrieved.astimezone(
        ZoneInfo("Asia/Kolkata")
    )

    weekday = local_time.weekday()
    minutes_of_day = (
        local_time.hour * 60
        + local_time.minute
        + local_time.second / 60
    )

    market_open = 9 * 60 + 15
    market_close = 15 * 60 + 30

    is_weekend = weekday >= 5
    is_market_hours = (
        not is_weekend
        and market_open <= minutes_of_day <= market_close
    )

    # During market hours, freshness is judged strictly.
    if is_market_hours:

        if age_minutes <= 30:
            return {
                "status": "Fresh",
                "label": "?? Fresh",
                "age_minutes": round(age_minutes, 1),
                "message": "Data was retrieved recently during market hours.",
            }

        if age_minutes <= 120:
            return {
                "status": "Aging",
                "label": "?? Aging",
                "age_minutes": round(age_minutes, 1),
                "message": "Data is older than the preferred freshness window.",
            }

        return {
            "status": "Potentially stale",
            "label": "?? Potentially stale",
            "age_minutes": round(age_minutes, 1),
            "message": "Data may no longer represent the latest market state.",
        }

    # Outside market hours, the latest available market observation
    # is not automatically considered stale.
    if age_minutes <= 24 * 60:
        return {
            "status": "Latest available",
            "label": "?? Latest available",
            "age_minutes": round(age_minutes, 1),
            "message": (
                "The exchange is outside normal market hours. "
                "This is the latest available provider observation."
            ),
        }

    return {
        "status": "Potentially stale",
        "label": "?? Potentially stale",
        "age_minutes": round(age_minutes, 1),
        "message": "The latest available observation is more than one day old.",
    }

from src.investment_guru.data.data_freshness import classify_data_freshness


def test_missing_timestamp_is_unavailable():
    result = classify_data_freshness(None)
    assert result["status"] == "Unavailable"


def test_recent_market_data_is_fresh():
    result = classify_data_freshness("2026-10-03T10:00:00+00:00")
    assert result["status"] in {
        "Fresh",
        "Aging",
        "Potentially stale",
        "Latest available",
    }


def test_invalid_timestamp_is_unavailable():
    result = classify_data_freshness("not-a-timestamp")
    assert result["status"] == "Unavailable"

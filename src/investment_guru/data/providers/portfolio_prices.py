from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf


def _build_result(
    ticker: str,
    current_price: float,
    source: str,
    currency: str | None = None,
    exchange: str | None = None,
    message: str = "",
) -> dict[str, Any]:

    return {
        "ticker": ticker,
        "current_price": round(
            float(current_price),
            4,
        ),
        "currency": currency,
        "exchange": exchange,
        "source": source,
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "OK",
        "message": message,
    }


def get_current_price(
    ticker: str,
) -> dict[str, Any]:
    """
    Fetch the latest available market price.

    Retrieval order:

    1. yfinance fast_info
    2. Recent intraday history
    3. Recent daily history

    No price is estimated or substituted.

    If intraday data is unavailable, the function may
    return the latest available daily closing price.
    """

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError(
            "Ticker cannot be empty."
        )

    stock = yf.Ticker(ticker)

    # ---------------------------------------------------------
    # METHOD 1: FAST INFO
    # ---------------------------------------------------------

    try:

        fast_info = stock.fast_info

        current_price = fast_info.get(
            "last_price"
        )

        if current_price is not None:

            current_price = float(
                current_price
            )

            if current_price > 0:

                return _build_result(
                    ticker=ticker,
                    current_price=current_price,
                    currency=fast_info.get(
                        "currency"
                    ),
                    exchange=fast_info.get(
                        "exchange"
                    ),
                    source="Yahoo Finance",
                    message=(
                        "Latest available market "
                        "price retrieved successfully."
                    ),
                )

    except Exception:
        pass

    # ---------------------------------------------------------
    # METHOD 2: RECENT INTRADAY HISTORY
    # ---------------------------------------------------------

    try:

        history = stock.history(
            period="5d",
            interval="5m",
            auto_adjust=False,
            prepost=False,
        )

        if not history.empty:

            close_prices = (
                history["Close"]
                .dropna()
            )

            if not close_prices.empty:

                current_price = float(
                    close_prices.iloc[-1]
                )

                if current_price > 0:

                    return _build_result(
                        ticker=ticker,
                        current_price=current_price,
                        source=(
                            "Yahoo Finance "
                            "intraday history"
                        ),
                        message=(
                            "Latest available "
                            "intraday market price "
                            "retrieved successfully."
                        ),
                    )

    except Exception:
        pass

    # ---------------------------------------------------------
    # METHOD 3: DAILY HISTORY FALLBACK
    # ---------------------------------------------------------

    try:

        history = stock.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            prepost=False,
        )

        if not history.empty:

            close_prices = (
                history["Close"]
                .dropna()
            )

            if not close_prices.empty:

                current_price = float(
                    close_prices.iloc[-1]
                )

                if current_price > 0:

                    return _build_result(
                        ticker=ticker,
                        current_price=current_price,
                        source=(
                            "Yahoo Finance "
                            "daily history"
                        ),
                        message=(
                            "Latest available "
                            "daily closing price "
                            "retrieved successfully. "
                            "Intraday data was unavailable."
                        ),
                    )

    except Exception:
        pass

    # ---------------------------------------------------------
    # FAILURE
    # ---------------------------------------------------------

    return {
        "ticker": ticker,
        "current_price": None,
        "currency": None,
        "exchange": None,
        "source": "Yahoo Finance",
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "UNAVAILABLE",
        "message": (
            "Current market price could not be "
            "retrieved. No price has been estimated "
            "or substituted."
        ),
    }
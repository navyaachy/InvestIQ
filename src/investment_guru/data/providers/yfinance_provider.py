from __future__ import annotations

from datetime import date

import yfinance as yf

from src.investment_guru.data.providers.base import DataProvider
from src.investment_guru.domain.models import PriceSeries


class YFinanceProvider(DataProvider):
    """Yahoo Finance adapter for Indian equities and benchmarks."""

    def _normalise_ticker(self, ticker: str) -> str:
        ticker = ticker.strip().upper()

        if ticker == "NIFTY50":
            return "^NSEI"

        if ticker.startswith("^"):
            return ticker

        if not ticker.endswith(".NS"):
            return f"{ticker}.NS"

        return ticker

    def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> PriceSeries:
        yahoo_ticker = self._normalise_ticker(ticker)

        data = yf.download(
            yahoo_ticker,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
        )

        if data.empty:
            raise ValueError(
                f"No market data returned for ticker: {yahoo_ticker}"
            )

        # yfinance can return MultiIndex columns for some downloads.
        if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
            data.columns = data.columns.get_level_values(0)

        required_columns = ["Open", "High", "Low", "Close", "Volume"]

        missing_columns = [
            column for column in required_columns
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns for {yahoo_ticker}: "
                f"{missing_columns}"
            )

        data = data[required_columns].copy()
        data.index.name = "Date"
        data = data.sort_index()

        return PriceSeries(
            ticker=yahoo_ticker,
            start_date=data.index.min().date(),
            end_date=data.index.max().date(),
            data=data,
        )
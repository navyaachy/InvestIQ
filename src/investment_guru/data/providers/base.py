from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from src.investment_guru.domain.models import PriceSeries


class DataProvider(ABC):
    """Abstract interface for market-data providers."""

    @abstractmethod
    def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> PriceSeries:
        """Return historical OHLCV data for a ticker."""
        raise NotImplementedError
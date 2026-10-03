from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class QualityStatus(str, Enum):
    OK = "OK"
    UNAVAILABLE = "UNAVAILABLE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


class PriceSeries(BaseModel):
    """Validated container for historical OHLCV price data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str
    start_date: date
    end_date: date
    data: pd.DataFrame

    @property
    def is_empty(self) -> bool:
        return self.data.empty

    @property
    def row_count(self) -> int:
        return len(self.data)


class MetricResult(BaseModel):
    """Standard result contract for a calculated metric."""

    name: str
    value: float | None = None
    unit: str | None = None
    status: QualityStatus = QualityStatus.OK
    explanation: str | None = None


class QualityReport(BaseModel):
    """Summary of data-quality checks."""

    ticker: str
    status: QualityStatus
    checks: dict[str, bool] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """Input contract for an InvestIQ analysis request."""

    ticker: str
    benchmark: str = "^NSEI"
    start_date: date | None = None
    end_date: date | None = None
    min_history_days: int = 252


class AnalysisResult(BaseModel):
    """Top-level response returned by the analysis pipeline."""

    ticker: str
    benchmark: str
    stock_data: PriceSeries | None = None
    benchmark_data: PriceSeries | None = None
    stock_quality: QualityReport | None = None
    benchmark_quality: QualityReport | None = None
    metrics: list[MetricResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
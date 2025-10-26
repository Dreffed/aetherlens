"""
Metric models for API.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    """Model for creating a metric."""

    device_id: str = Field(..., description="Device ID")
    metric_type: str = Field(..., description="Metric type (e.g., 'power', 'energy')")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    tags: dict[str, str] | None = Field(None, description="Additional tags")


class MetricResponse(BaseModel):
    """Model for metric API response."""

    time: datetime
    device_id: str
    metric_type: str
    value: float
    unit: str
    tags: dict[str, str] | None = None

    class Config:
        from_attributes = True


class MetricQueryParams(BaseModel):
    """Model for metric query parameters."""

    device_id: str | None = Field(None, description="Filter by device ID")
    metric_type: str | None = Field(None, description="Filter by metric type")
    start_time: datetime | None = Field(None, description="Start time for query")
    end_time: datetime | None = Field(None, description="End time for query")
    limit: int = Field(1000, ge=1, le=10000, description="Maximum results")


class MetricAggregateResponse(BaseModel):
    """Model for aggregated metrics response."""

    device_id: str
    metric_type: str
    bucket: datetime
    avg_value: float
    min_value: float
    max_value: float
    count: int

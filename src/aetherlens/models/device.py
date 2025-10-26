"""
Device models for API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DeviceBase(BaseModel):
    """Base device model with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    type: str = Field(..., description="Device type (e.g., 'smart_plug', 'solar_inverter')")
    manufacturer: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    location: dict[str, Any] | None = Field(
        None, description="Location metadata (room, floor, etc.)"
    )
    capabilities: list[str] = Field(default_factory=list, description="Device capabilities")


class DeviceCreate(DeviceBase):
    """Model for creating a device."""

    device_id: str = Field(
        ..., min_length=1, max_length=100, description="Unique device identifier"
    )
    configuration: dict[str, Any] | None = Field(None, description="Device configuration")

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        """Validate device ID format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Device ID must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v


class DeviceUpdate(BaseModel):
    """Model for updating a device."""

    name: str | None = Field(None, min_length=1, max_length=255)
    type: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    location: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    capabilities: list[str] | None = None


class DeviceResponse(DeviceBase):
    """Model for device API response."""

    device_id: str
    manufacturer: str | None = None
    model: str | None = None
    location: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    status: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Model for paginated device list response."""

    devices: list[DeviceResponse]
    total: int
    page: int
    page_size: int
    pages: int

"""
Device models for API.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, field_validator


class DeviceBase(BaseModel):
    """Base device model with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    type: str = Field(..., description="Device type (e.g., 'smart_plug', 'solar_inverter')")
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    location: Optional[Dict[str, Any]] = Field(None, description="Location metadata (room, floor, etc.)")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")


class DeviceCreate(DeviceBase):
    """Model for creating a device."""
    device_id: str = Field(..., min_length=1, max_length=100, description="Unique device identifier")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Device configuration")

    @field_validator('device_id')
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        """Validate device ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Device ID must contain only alphanumeric characters, hyphens, and underscores")
        return v


class DeviceUpdate(BaseModel):
    """Model for updating a device."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None


class DeviceResponse(DeviceBase):
    """Model for device API response."""
    device_id: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Model for paginated device list response."""
    devices: List[DeviceResponse]
    total: int
    page: int
    page_size: int
    pages: int

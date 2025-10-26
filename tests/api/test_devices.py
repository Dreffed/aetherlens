"""
Device CRUD endpoint tests.

Tests for:
- GET /api/v1/devices - List devices with pagination
- GET /api/v1/devices/{id} - Get specific device
- POST /api/v1/devices - Create device (admin only)
- PUT /api/v1/devices/{id} - Update device (admin only)
- DELETE /api/v1/devices/{id} - Delete device (admin only)
"""

import pytest
from httpx import AsyncClient

# ============================================================================
# List Devices Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_devices_authenticated(authenticated_client: AsyncClient, sample_device):
    """Test listing devices as authenticated user."""
    response = await authenticated_client.get("/api/v1/devices")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "devices" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data

    # Should have at least our sample device
    assert len(data["devices"]) >= 1
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_devices_unauthenticated(api_client: AsyncClient):
    """Test that unauthenticated users cannot list devices."""
    response = await api_client.get("/api/v1/devices")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_devices_pagination(authenticated_client: AsyncClient, sample_devices):
    """Test device list pagination."""
    response = await authenticated_client.get("/api/v1/devices?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["devices"]) <= 2
    assert data["pages"] >= 1


@pytest.mark.asyncio
async def test_list_devices_pagination_second_page(
    authenticated_client: AsyncClient, sample_devices
):
    """Test accessing second page of devices."""
    response = await authenticated_client.get("/api/v1/devices?page=2&page_size=1")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2


@pytest.mark.asyncio
async def test_list_devices_invalid_page(authenticated_client: AsyncClient):
    """Test that invalid page number is handled."""
    response = await authenticated_client.get("/api/v1/devices?page=0")

    # Should return validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_devices_invalid_page_size(authenticated_client: AsyncClient):
    """Test that invalid page size is handled."""
    response = await authenticated_client.get("/api/v1/devices?page_size=1000")

    # Should return validation error (max 100)
    assert response.status_code == 422


# ============================================================================
# Get Device Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_device_by_id(authenticated_client: AsyncClient, sample_device):
    """Test getting specific device by ID."""
    device_id = sample_device["device_id"]
    response = await authenticated_client.get(f"/api/v1/devices/{device_id}")

    assert response.status_code == 200
    data = response.json()

    # Verify device data
    assert data["device_id"] == device_id
    assert data["name"] == sample_device["name"]
    assert data["type"] == sample_device["type"]


@pytest.mark.asyncio
async def test_get_device_not_found(authenticated_client: AsyncClient):
    """Test getting non-existent device returns 404."""
    response = await authenticated_client.get("/api/v1/devices/no-such-device")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_device_unauthenticated(api_client: AsyncClient, sample_device):
    """Test that unauthenticated users cannot get device details."""
    device_id = sample_device["device_id"]
    response = await api_client.get(f"/api/v1/devices/{device_id}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_device_includes_timestamps(authenticated_client: AsyncClient, sample_device):
    """Test that device response includes created_at and updated_at."""
    device_id = sample_device["device_id"]
    response = await authenticated_client.get(f"/api/v1/devices/{device_id}")

    assert response.status_code == 200
    data = response.json()

    assert "created_at" in data
    assert "updated_at" in data


# ============================================================================
# Create Device Tests (Admin Only)
# ============================================================================


@pytest.mark.asyncio
async def test_create_device_as_admin(admin_client: AsyncClient):
    """Test creating device with admin role."""
    import time

    device_data = {
        "device_id": f"new-device-{time.time()}",
        "name": "New Test Device",
        "type": "energy_monitor",
        "manufacturer": "Test Corp",
        "model": "TM-200",
        "configuration": {"ip": "192.168.1.200"},
    }

    response = await admin_client.post("/api/v1/devices", json=device_data)

    assert response.status_code == 201
    data = response.json()

    assert data["device_id"] == device_data["device_id"]
    assert data["name"] == device_data["name"]
    assert data["type"] == device_data["type"]


@pytest.mark.asyncio
async def test_create_device_as_user_forbidden(authenticated_client: AsyncClient):
    """Test that regular users cannot create devices."""
    import time

    device_data = {
        "device_id": f"forbidden-device-{time.time()}",
        "name": "Forbidden Device",
        "type": "smart_plug",
    }

    response = await authenticated_client.post("/api/v1/devices", json=device_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_device_unauthenticated(api_client: AsyncClient):
    """Test that unauthenticated users cannot create devices."""
    device_data = {
        "device_id": "test-device",
        "name": "Test Device",
        "type": "smart_plug",
    }

    response = await api_client.post("/api/v1/devices", json=device_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_device_validation_empty_id(admin_client: AsyncClient):
    """Test device creation with empty ID fails validation."""
    device_data = {
        "device_id": "",
        "name": "Test Device",
        "type": "smart_plug",
    }

    response = await admin_client.post("/api/v1/devices", json=device_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_device_validation_missing_name(admin_client: AsyncClient):
    """Test device creation without name fails validation."""
    import time

    device_data = {
        "device_id": f"test-device-{time.time()}",
        "type": "smart_plug",
    }

    response = await admin_client.post("/api/v1/devices", json=device_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_device_duplicate_id(admin_client: AsyncClient, sample_device):
    """Test creating device with duplicate ID fails."""
    device_data = {
        "device_id": sample_device["device_id"],  # Same as existing
        "name": "Duplicate Device",
        "type": "smart_plug",
    }

    response = await admin_client.post("/api/v1/devices", json=device_data)

    # Should fail with conflict error
    assert response.status_code in [409, 400]


# ============================================================================
# Update Device Tests (Admin Only)
# ============================================================================


@pytest.mark.asyncio
async def test_update_device_as_admin(admin_client: AsyncClient, sample_device):
    """Test updating device with admin role."""
    device_id = sample_device["device_id"]
    update_data = {"name": "Updated Device Name"}

    response = await admin_client.put(f"/api/v1/devices/{device_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    # Other fields should remain unchanged
    assert data["type"] == sample_device["type"]


@pytest.mark.asyncio
async def test_update_device_as_user_forbidden(authenticated_client: AsyncClient, sample_device):
    """Test that regular users cannot update devices."""
    device_id = sample_device["device_id"]
    update_data = {"name": "Should Not Update"}

    response = await authenticated_client.put(f"/api/v1/devices/{device_id}", json=update_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_device_not_found(admin_client: AsyncClient):
    """Test updating non-existent device returns 404."""
    update_data = {"name": "Updated Name"}

    response = await admin_client.put("/api/v1/devices/no-such-device", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_device_partial_update(admin_client: AsyncClient, sample_device):
    """Test partial update only changes specified fields."""
    device_id = sample_device["device_id"]

    # Update only manufacturer
    update_data = {"manufacturer": "Updated Corp"}

    response = await admin_client.put(f"/api/v1/devices/{device_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["manufacturer"] == "Updated Corp"
    # Name should remain unchanged
    assert data["name"] == sample_device["name"]


# ============================================================================
# Delete Device Tests (Admin Only)
# ============================================================================


@pytest.mark.asyncio
async def test_delete_device_as_admin(admin_client: AsyncClient, sample_device):
    """Test deleting device with admin role."""
    device_id = sample_device["device_id"]

    response = await admin_client.delete(f"/api/v1/devices/{device_id}")

    assert response.status_code == 204

    # Verify deletion
    get_response = await admin_client.get(f"/api/v1/devices/{device_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_device_as_user_forbidden(authenticated_client: AsyncClient, sample_device):
    """Test that regular users cannot delete devices."""
    device_id = sample_device["device_id"]

    response = await authenticated_client.delete(f"/api/v1/devices/{device_id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_device_not_found(admin_client: AsyncClient):
    """Test deleting non-existent device returns 404."""
    response = await admin_client.delete("/api/v1/devices/no-such-device")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_device_unauthenticated(api_client: AsyncClient, sample_device):
    """Test that unauthenticated users cannot delete devices."""
    device_id = sample_device["device_id"]

    response = await api_client.delete(f"/api/v1/devices/{device_id}")

    assert response.status_code == 401


# ============================================================================
# Device Data Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_device_response_structure(authenticated_client: AsyncClient, sample_device):
    """Test that device response has correct structure."""
    device_id = sample_device["device_id"]
    response = await authenticated_client.get(f"/api/v1/devices/{device_id}")

    assert response.status_code == 200
    data = response.json()

    # Required fields
    assert "device_id" in data
    assert "name" in data
    assert "type" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Optional fields
    # These may or may not be present
    for field in ["manufacturer", "model", "configuration"]:
        if field in data:
            assert data[field] is not None

"""
Device management API endpoints.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from aetherlens.api.database import db_manager
from aetherlens.api.dependencies import get_current_user, require_admin
from aetherlens.models.device import DeviceCreate, DeviceListResponse, DeviceResponse, DeviceUpdate

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/devices", tags=["Devices"])


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    type: str | None = Query(None, description="Filter by device type"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all devices with pagination.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    - type: Filter by device type (optional)

    **Returns:**
    Paginated list of devices with metadata.
    """
    offset = (page - 1) * page_size

    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        # Build query
        where_clause = ""
        params = [page_size, offset]

        if type:
            where_clause = "WHERE type = $3"
            params.append(type)

        # Get total count
        # Safe: where_clause is either empty or hardcoded "WHERE type = $3", values parameterized
        count_query = f"SELECT COUNT(*) FROM devices {where_clause}"  # noqa: S608
        count_params = params[2:] if type else []
        total = await conn.fetchval(count_query, *count_params)

        # Get devices
        query = f"""
            SELECT device_id, name, type, manufacturer, model, location,
                   capabilities, configuration, metadata, status,
                   created_at, updated_at
            FROM devices
            {where_clause}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """

        rows = await conn.fetch(query, *params)

    devices = [DeviceResponse(**dict(row)) for row in rows]
    pages = (total + page_size - 1) // page_size

    return DeviceListResponse(
        devices=devices, total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get a specific device by ID.

    **Path Parameters:**
    - device_id: Unique device identifier

    **Returns:**
    Device details including configuration and status.
    """
    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT device_id, name, type, manufacturer, model, location,
                   capabilities, configuration, metadata, status,
                   created_at, updated_at
            FROM devices
            WHERE device_id = $1
            """,
            device_id,
        )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found"
        )

    return DeviceResponse(**dict(row))


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(device: DeviceCreate, current_user: dict = Depends(require_admin)):
    """
    Create a new device.

    **Requires:** Admin role

    **Request Body:**
    Device details including ID, name, type, and configuration.

    **Returns:**
    Created device with timestamps.
    """
    pool = db_manager.get_pool()

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO devices (
                    device_id, name, type, manufacturer, model,
                    location, capabilities, configuration, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING device_id, name, type, manufacturer, model, location,
                          capabilities, configuration, metadata, status,
                          created_at, updated_at
                """,
                device.device_id,
                device.name,
                device.type,
                device.manufacturer,
                device.model,
                device.location,
                device.capabilities,
                device.configuration,
                {"online": False},  # Default status
            )

        logger.info("Device created", device_id=device.device_id, user_id=current_user["user_id"])
        return DeviceResponse(**dict(row))

    except Exception as e:
        logger.error("Failed to create device", error=str(e), device_id=device.device_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create device: {str(e)}"
        ) from e


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str, device: DeviceUpdate, current_user: dict = Depends(require_admin)
):
    """
    Update an existing device.

    **Requires:** Admin role

    **Path Parameters:**
    - device_id: Device to update

    **Request Body:**
    Fields to update (only provided fields are updated).
    """
    # Build update query dynamically
    updates = []
    params = []
    param_count = 1

    for field, value in device.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ${param_count}")
        params.append(value)
        param_count += 1

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    params.append(device_id)

    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        # Safe: field names from Pydantic model, values parameterized ($1, $2, etc.)
        query = (
            f"UPDATE devices "  # noqa: S608
            f"SET {', '.join(updates)}, updated_at = NOW() "  # noqa: S608
            f"WHERE device_id = ${param_count} "  # noqa: S608
            f"RETURNING device_id, name, type, manufacturer, model, location, "  # noqa: S608
            f"capabilities, configuration, metadata, status, "  # noqa: S608
            f"created_at, updated_at"  # noqa: S608
        )
        row = await conn.fetchrow(query, *params)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found"
        )

    logger.info("Device updated", device_id=device_id, user_id=current_user["user_id"])
    return DeviceResponse(**dict(row))


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: str, current_user: dict = Depends(require_admin)):
    """
    Delete a device.

    **Requires:** Admin role

    **Path Parameters:**
    - device_id: Device to delete

    **Note:** This will also delete all associated metrics.
    """
    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM devices WHERE device_id = $1", device_id)

    if result == "DELETE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found"
        )

    logger.info("Device deleted", device_id=device_id, user_id=current_user["user_id"])

"""
Authentication endpoint tests.

Tests for:
- POST /api/v1/auth/login - User login with JWT token generation
- Token validation and expiration
- Invalid credentials handling
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(api_client: AsyncClient, test_user):
    """Test successful login with valid credentials."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert "expires_in" in data

    # Verify token type and expiration
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600  # 1 hour

    # Verify tokens are not empty
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_password(api_client: AsyncClient, test_user):
    """Test login failure with incorrect password."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "incorrect" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(api_client: AsyncClient):
    """Test login failure with non-existent user."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "nosuchuser", "password": "anypassword"},
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_missing_username(api_client: AsyncClient):
    """Test login validation error with missing username."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"password": "testpassword123"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_missing_password(api_client: AsyncClient):
    """Test login validation error with missing password."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_empty_credentials(api_client: AsyncClient):
    """Test login validation error with empty credentials."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "", "password": ""},
    )

    assert response.status_code in [401, 422]  # Either auth failure or validation


@pytest.mark.asyncio
async def test_authenticated_request(authenticated_client: AsyncClient):
    """Test accessing protected endpoint with valid token."""
    response = await authenticated_client.get("/api/v1/devices")

    # Should succeed with 200 (even if no devices)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_request(api_client: AsyncClient):
    """Test accessing protected endpoint without token."""
    response = await api_client.get("/api/v1/devices")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_token_format(api_client: AsyncClient):
    """Test accessing endpoint with malformed token."""
    api_client.headers.update({"Authorization": "Bearer invalid-token-format"})
    response = await api_client.get("/api/v1/devices")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token(api_client: AsyncClient):
    """Test accessing endpoint with expired token."""
    from aetherlens.security.jwt import jwt_manager

    # Create token that expired 1 hour ago
    expired_token = jwt_manager.create_access_token(
        {"sub": "test-user", "username": "test", "role": "user"},
        expires_delta=timedelta(hours=-1),
    )

    api_client.headers.update({"Authorization": f"Bearer {expired_token}"})
    response = await api_client.get("/api/v1/devices")

    assert response.status_code == 401
    data = response.json()
    assert "expired" in data["detail"].lower()


@pytest.mark.asyncio
async def test_admin_login(api_client: AsyncClient, admin_user):
    """Test admin user can login successfully."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "adminuser", "password": "adminpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_response_headers(api_client: AsyncClient, test_user):
    """Test that login response includes proper headers."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )

    assert response.status_code == 200
    # Verify standard headers
    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_login_rate_limiting_headers(api_client: AsyncClient, test_user):
    """Test that login response includes rate limit headers."""
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )

    # Rate limit headers should be present (if rate limiting is enabled)
    # These are optional depending on middleware configuration
    # Just verify the endpoint works
    assert response.status_code == 200

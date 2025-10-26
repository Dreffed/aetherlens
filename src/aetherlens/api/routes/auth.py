"""
Authentication routes for token generation.
"""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from aetherlens.api.database import db_manager
from aetherlens.security.jwt import jwt_manager
from aetherlens.security.passwords import verify_password

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    **Example Request:**
    ```json
    {
      "username": "admin",
      "password": "password"
    }
    ```

    **Returns:**
    - access_token: Short-lived token for API access
    - refresh_token: Long-lived token for renewing access
    """
    # Fetch user from database
    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT user_id, username, email, password_hash, role
            FROM users
            WHERE username = $1
            """,
            request.username,
        )

    # Verify user exists
    if user is None:
        logger.warning("Login failed - user not found", username=request.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        logger.warning("Login failed - invalid password", username=request.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    token_data = {"sub": user["user_id"], "username": user["username"], "role": user["role"]}

    access_token = jwt_manager.create_access_token(token_data)
    refresh_token = jwt_manager.create_refresh_token({"sub": user["user_id"]})

    logger.info("User logged in", user_id=user["user_id"], username=user["username"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60,  # 1 hour in seconds
    )

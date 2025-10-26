"""
FastAPI dependencies for authentication and authorization.
"""

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aetherlens.api.database import db_manager
from aetherlens.security.jwt import jwt_manager

logger = structlog.get_logger()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User information dictionary

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Decode token
    payload = jwt_manager.decode_token(token)

    # Extract user ID
    user_id: str | None = payload.get("sub")
    if user_id is None:
        logger.error("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT user_id, username, email, role FROM users WHERE user_id = $1", user_id
        )

    if user is None:
        logger.error("User not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return dict(user)


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to require admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User information if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.get("role") != "admin":
        logger.warning("Admin access denied", user_id=current_user.get("user_id"))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return current_user

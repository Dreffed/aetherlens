"""
JWT token management for authentication.
"""

from datetime import datetime, timedelta
from typing import Any

import jwt
import structlog
from fastapi import HTTPException, status

from aetherlens.config import settings

logger = structlog.get_logger()


class JWTManager:
    """Manages JWT token creation and validation."""

    def create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload data to encode
            expires_delta: Token expiration time (default from settings)

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

        logger.info("Access token created", user_id=data.get("sub"), expires_at=expire.isoformat())
        return encoded_jwt

    def create_refresh_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()

        if expires_delta is None:
            expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

        except jwt.JWTError as e:
            logger.error("Token validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e


jwt_manager = JWTManager()

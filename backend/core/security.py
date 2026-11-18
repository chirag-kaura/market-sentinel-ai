"""
Authentication, Security, and Role-Based Access Control (RBAC).
Phase 10 — Step 10.5: Implements password hashing, JWT token creation/validation, and RBAC guards.
"""

import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from backend.core.exceptions import SurveillanceAPIException

# Secret configuration (environment with secure fallbacks)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "market-sentinel-dev-insecure-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    username: str
    roles: List[str]
    exp: datetime


class User(BaseModel):
    username: str
    hashed_password: str
    roles: List[str]
    is_active: bool = True


def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with SHA256 (CPU-friendly, no external compiled deps)."""
    salt = b"market_sentinel_salt_constant"
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
    return key.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed value using constant-time comparison."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


# Seed users database
USER_DATABASE: Dict[str, User] = {
    "analyst1": User(
        username="analyst1",
        hashed_password=hash_password("analyst_password123"),
        roles=["ANALYST"],
    ),
    "admin1": User(
        username="admin1",
        hashed_password=hash_password("admin_password123"),
        roles=["ADMIN", "ANALYST"],
    ),
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT access token signature and expiration."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_EXPIRED",
            message="Access token has expired. Please log in again.",
        )
    except jwt.PyJWTError:
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_TOKEN",
            message="Could not validate credentials.",
        )


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> User:
    """FastAPI dependency to extract and authenticate current user from Bearer token."""
    if not credentials:
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="MISSING_TOKEN",
            message="Authorization bearer token required.",
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    if username is None or username not in USER_DATABASE:
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="USER_NOT_FOUND",
            message="Authenticated user not found.",
        )

    user = USER_DATABASE[username]
    if not user.is_active:
        raise SurveillanceAPIException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="USER_INACTIVE",
            message="User account is inactive.",
        )
    return user


class RoleChecker:
    """RBAC guard verifying user belongs to authorized role groups."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not any(role in self.allowed_roles for role in user.roles):
            raise SurveillanceAPIException(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="FORBIDDEN_INSUFFICIENT_PERMISSIONS",
                message=f"Operation requires one of the following roles: {self.allowed_roles}",
            )
        return user

"""
Authentication, Security, and Role-Based Access Control (RBAC).
Phase 10 — Step 10.5: Implements password hashing, JWT token creation/validation, and RBAC guards.
Aligned with BRD FR-7.3 Persona Hierarchy:
- READ_ONLY_ANALYST: Read-only surveillance monitoring.
- ANALYST: Investigative analyst (notes, triage, case initiation).
- COMPLIANCE_OFFICER: Senior compliance officer (SAR escalations, alert dismissals, case sign-off).
- ADMIN: Platform administrator (audit logs, user management, system health).
"""

import os
import hashlib
import hmac
import secrets
from enum import Enum
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
PBKDF2_ITERATIONS = 100000
LEGACY_SALT = b"market_sentinel_salt_constant"

security_scheme = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """Institutional surveillance RBAC personas per BRD FR-7.3."""
    READ_ONLY_ANALYST = "READ_ONLY_ANALYST"
    ANALYST = "ANALYST"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    ADMIN = "ADMIN"


class TokenPayload(BaseModel):
    username: str
    roles: List[str]
    exp: datetime


class User(BaseModel):
    username: str
    hashed_password: str
    roles: List[str]
    is_active: bool = True


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """
    Hash password using PBKDF2 with SHA256 and unique per-user cryptographic salt.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed value using constant-time comparison."""
    if not hashed_password:
        return False

    # Check for modern formatted hash
    if hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) == 4:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected_key = parts[3]
            computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations).hex()
            return hmac.compare_digest(computed_key, expected_key)

    # Legacy fallback for backward compatibility
    legacy_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), LEGACY_SALT, 10000).hex()
    return hmac.compare_digest(legacy_key, hashed_password)


# Seed users database covering the full BRD persona hierarchy
USER_DATABASE: Dict[str, User] = {
    "viewer1": User(
        username="viewer1",
        hashed_password=hash_password("viewer_password123"),
        roles=[UserRole.READ_ONLY_ANALYST.value],
    ),
    "analyst1": User(
        username="analyst1",
        hashed_password=hash_password("analyst_password123"),
        roles=[UserRole.ANALYST.value, UserRole.READ_ONLY_ANALYST.value],
    ),
    "officer1": User(
        username="officer1",
        hashed_password=hash_password("officer_password123"),
        roles=[UserRole.COMPLIANCE_OFFICER.value, UserRole.ANALYST.value, UserRole.READ_ONLY_ANALYST.value],
    ),
    "admin1": User(
        username="admin1",
        hashed_password=hash_password("admin_password123"),
        roles=[UserRole.ADMIN.value, UserRole.COMPLIANCE_OFFICER.value, UserRole.ANALYST.value, UserRole.READ_ONLY_ANALYST.value],
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


def get_user_from_token(token: str) -> User:
    """Validate token string and return user object."""
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


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> User:
    """FastAPI dependency to extract and authenticate current user from Bearer token."""
    if not credentials:
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="MISSING_TOKEN",
            message="Authorization bearer token required.",
        )

    return get_user_from_token(credentials.credentials)


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

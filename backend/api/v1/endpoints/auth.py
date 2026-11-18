"""
Authentication & Token RESTful API Endpoints.
Phase 10 — Step 10.5: Login and token verification endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from backend.core.security import (
    USER_DATABASE,
    create_access_token,
    verify_password,
    get_current_user,
    User,
    RoleChecker,
)
from backend.core.exceptions import SurveillanceAPIException

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    roles: list


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Authenticate user credentials and issue signed JWT access token."""
    user = USER_DATABASE.get(request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise SurveillanceAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
            message="Incorrect username or password.",
        )

    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles}
    )
    return TokenResponse(
        access_token=access_token,
        username=user.username,
        roles=user.roles,
    )


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile and permissions for currently authenticated user."""
    return {
        "username": current_user.username,
        "roles": current_user.roles,
        "is_active": current_user.is_active,
    }


@router.get("/admin/audit", dependencies=[Depends(RoleChecker(["ADMIN"]))])
def get_admin_audit_log():
    """Restricted endpoint accessible exclusively to ADMIN roles."""
    return {"status": "ok", "message": "Admin surveillance audit logs accessed successfully."}

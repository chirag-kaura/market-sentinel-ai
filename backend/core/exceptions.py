"""
Domain Exceptions and Global Error Handlers.
Phase 10 — Step 10.1: Defines standard HTTP-aware exceptions and structured error payloads.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorResponseSchema(BaseModel):
    """Standardized error envelope returned by all API endpoints on failure."""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=lambda: __import__("time").time())


class SurveillanceAPIException(HTTPException):
    """Base application exception for surveillance API domain errors."""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class EntityNotFoundError(SurveillanceAPIException):
    """Raised when an equity symbol, alert, or document chunk is not found."""
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ENTITY_NOT_FOUND",
            message=f"{entity_name} with identifier '{entity_id}' was not found.",
            details={"entity_name": entity_name, "entity_id": entity_id}
        )


class SurveillanceValidationError(SurveillanceAPIException):
    """Raised when incoming analysis or backtest parameters fail validation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details
        )


async def surveillance_exception_handler(request: Request, exc: SurveillanceAPIException) -> JSONResponse:
    """FastAPI exception handler for domain SurveillanceAPIException instances."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseSchema(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).model_dump()
    )


async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler catching unhandled exceptions to prevent stack trace leaks."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponseSchema(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            details={"error_type": exc.__class__.__name__}
        ).model_dump()
    )

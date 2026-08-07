from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base domain exception for application business logic failures."""
    def __init__(self, detail: str, code: str = "DOMAIN_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


class ResourceNotFoundException(DomainException):
    """Raised when a requested entity or resource is not found."""
    def __init__(self, resource_name: str, identifier: Any):
        super().__init__(
            detail=f"{resource_name} with identifier '{identifier}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(DomainException):
    """Raised when a database constraint or unique key conflict occurs."""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            code="RESOURCE_CONFLICT",
            status_code=status.HTTP_409_CONFLICT
        )


class CapacityExceededException(DomainException):
    """Raised when a workload or section capacity cap is exceeded."""
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            code="CAPACITY_EXCEEDED",
            status_code=status.HTTP_400_BAD_REQUEST
        )


async def rfc7807_domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Standard RFC 7807 Problem Details JSON exception handler for domain exceptions."""
    problem_details = {
        "type": f"https://vfstr.ac.in/errors/{exc.code.lower()}",
        "title": exc.code.replace("_", " ").title(),
        "status": exc.status_code,
        "detail": exc.detail,
        "code": exc.code,
        "instance": str(request.url),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(status_code=exc.status_code, content=problem_details)

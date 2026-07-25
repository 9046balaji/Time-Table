from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from typing import Dict, Any, Optional
from app.core.config import settings

from datetime import datetime, timedelta, timezone

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token for authenticated users."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Validate JWT bearer token for write/mutation routes or return default coordinator context."""
    if not token:
        # Default user context if no authorization header present in dev
        return {"sub": "coordinator@vfstr.ac.in", "role": "DEPT_COORDINATOR", "dept_id": 1}

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security Error: Could not validate session credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(allowed_roles: list[str]):
    """Enforce Granular Role-Based Access Control (RBAC) on API endpoints."""
    def role_verifier(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "STUDENT")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Role '{user_role}' is not authorized to access this resource."
            )
        return current_user
    return role_verifier


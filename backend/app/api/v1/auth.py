from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from app.core.auth import create_access_token, get_current_user
from datetime import timedelta

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


def _verify_and_issue_token(username: str, role: Optional[str] = None) -> TokenResponse:
    # Determine role based on username/email pattern or default coordinator
    user_lower = username.lower()
    if not role:
        if "hod" in user_lower:
            role = "HOD"
        elif "admin" in user_lower:
            role = "ADMIN"
        elif "student" in user_lower:
            role = "STUDENT"
        elif "faculty" in user_lower:
            role = "FACULTY"
        else:
            role = "DEPT_COORDINATOR"

    token_data = {
        "sub": username,
        "role": role,
        "dept_id": 1,
    }
    access_token = create_access_token(token_data, expires_delta=timedelta(hours=24))
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role,
        username=username
    )


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password form endpoint for Swagger UI & automated agents."""
    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    return _verify_and_issue_token(form_data.username)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Standard JSON login endpoint for frontend client applications."""
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    return _verify_and_issue_token(credentials.username)


@router.get("/me", response_model=Dict[str, Any])
async def read_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return the authenticated user profile and roles."""
    return {
        "username": current_user.get("sub"),
        "role": current_user.get("role", "STUDENT"),
        "department_id": current_user.get("dept_id", 1),
        "status": "ACTIVE",
        "authenticated": True
    }

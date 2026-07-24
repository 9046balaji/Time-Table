from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class FacultyBase(BaseModel):
    name: str = Field(..., example="Dr. S. Srikantha Reddy")
    designation: str = Field("Assistant Professor", example="Associate Professor")
    max_hours_per_week: int = Field(16, ge=1, le=30)
    availability: Optional[Dict[str, Any]] = None


class FacultyCreate(FacultyBase):
    dept_id: Optional[int] = None


class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    max_hours_per_week: Optional[int] = None
    availability: Optional[Dict[str, Any]] = None


class FacultyResponse(FacultyBase):
    id: int
    dept_id: Optional[int] = None
    hours_this_week: int = 0

    class Config:
        from_attributes = True

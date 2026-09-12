from pydantic import BaseModel, Field
from typing import Optional


class SubjectBase(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "DS"})
    name: str = Field(..., json_schema_extra={"example": "Data Structures"})
    type: str = Field("L", json_schema_extra={"example": "L"})  # L, P, T
    weekly_hours: int = Field(3, ge=1, le=10)


class SubjectCreate(SubjectBase):
    dept_id: Optional[int] = None


class SubjectResponse(SubjectBase):
    id: int
    dept_id: Optional[int] = None

    class Config:
        from_attributes = True

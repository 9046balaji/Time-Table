from pydantic import BaseModel, Field
from typing import Optional


class SubjectBase(BaseModel):
    code: str = Field(..., example="DS")
    name: str = Field(..., example="Data Structures")
    type: str = Field("L", example="L")  # L, P, T
    weekly_hours: int = Field(3, ge=1, le=10)


class SubjectCreate(SubjectBase):
    dept_id: Optional[int] = None


class SubjectResponse(SubjectBase):
    id: int
    dept_id: Optional[int] = None

    class Config:
        from_attributes = True

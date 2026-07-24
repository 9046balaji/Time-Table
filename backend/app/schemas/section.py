from pydantic import BaseModel, Field
from typing import Optional, List


class SectionBase(BaseModel):
    name: str = Field(..., example="II AIML-A")
    label: str = Field(..., example="II Year")
    strength: int = Field(60, ge=1, le=200)


class SectionCreate(SectionBase):
    branch_id: int
    academic_year_id: int


class SectionResponse(SectionBase):
    id: int
    branch_id: int
    academic_year_id: int
    branch_code: Optional[str] = "AIML"

    class Config:
        from_attributes = True

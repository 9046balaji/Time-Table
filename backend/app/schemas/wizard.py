from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CourseAssignmentInput(BaseModel):
    subject_code: str = Field(..., json_schema_extra={"example": "DS"})
    subject_name: str = Field(..., json_schema_extra={"example": "Data Structures"})
    subject_type: str = Field("L", json_schema_extra={"example": "L"})  # L, P, T
    faculty_name: str = Field(..., json_schema_extra={"example": "Dr. S. Srikantha Reddy"})  # Primary faculty
    co_faculty: List[str] = Field(default_factory=list, json_schema_extra={"example": ["P. Girija", "K. Nikhitha"]})  # Lab co-instructors
    weekly_hours: int = Field(3, ge=1, le=30)
    continuous_slots: int = Field(1, ge=1, le=3, json_schema_extra={"example": 2})  # 1 for theory, 2 or 3 for continuous labs


class TimetableGenerationRequest(BaseModel):
    branch: str = Field("AIML", json_schema_extra={"example": "AIML"})
    year_level: str = Field("II Year", json_schema_extra={"example": "II Year"})
    sections: List[str] = Field(default_factory=lambda: ["II AIML-A", "II AIML-B"])
    preferred_block: str = Field("Block-VI (601-619)", json_schema_extra={"example": "Block-VI (601-619)"})
    max_daily_teaching_hours: int = Field(5, ge=1, le=8)
    max_classes_per_teacher_per_day: int = Field(5, ge=1, le=8)
    rooms: Optional[List[Dict[str, Any]]] = Field(None, description="Optional custom room pool to override default building block list")
    assignments: List[CourseAssignmentInput] = Field(default_factory=list)



class WizardGenerationResponse(BaseModel):
    status: str
    runtime_seconds: float
    entries_count: int
    hard_violations: int
    soft_violations: int
    message: str
    version_id: Optional[int] = None
    entries: List[Dict[str, Any]]

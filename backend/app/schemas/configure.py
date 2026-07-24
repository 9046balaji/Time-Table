from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any


class FacultyCreate(BaseModel):
    name: str = Field(..., description="Faculty full name with title")
    employee_id: Optional[str] = Field(None, description="Unique institutional ID")
    dept_id: Optional[int] = Field(1, description="Department ID")
    designation: str = Field("Assistant Professor", description="Professor | Associate Professor | Assistant Professor")
    max_hours_per_week: int = Field(16, ge=1, le=30, description="Weekly hours limit")
    max_daily_classes: int = Field(5, ge=1, le=8, description="Max classes allowed per day")
    is_external: bool = Field(False, description="Industry or external instructor flag")
    availability: Optional[Dict[str, List[int]]] = Field(
        default_factory=lambda: {
            "MON": [1, 2, 3, 4, 5, 6, 7, 8],
            "TUE": [1, 2, 3, 4, 5, 6, 7, 8],
            "WED": [1, 2, 3, 4, 5, 6, 7, 8],
            "THU": [1, 2, 3, 4, 5, 6, 7, 8],
            "FRI": [1, 2, 3, 4, 5, 6, 7, 8],
            "SAT": [1, 2, 3, 4, 5, 6, 7, 8],
        },
        description="Availability grid: {'MON': [1,2,3...], ...}"
    )


class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    max_hours_per_week: Optional[int] = None
    max_daily_classes: Optional[int] = None
    is_external: Optional[bool] = None
    availability: Optional[Dict[str, List[int]]] = None


class FacultyResponse(FacultyCreate):
    id: int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    code: str = Field(..., description="Room code e.g. 601, 604, AFTF-12")
    dept_id: Optional[int] = Field(1, description="Department ID")
    room_type: str = Field("classroom", description="classroom | computer_lab | gpu_lab | project_room | seminar_hall")
    capacity: int = Field(60, ge=1, le=200, description="Student seating capacity")
    floor: Optional[str] = Field("6", description="Floor tag: 6, 5, AFTF, AFF, NB")
    block: str = Field("U-Block", description="Aryabhatta Bhavan / U-Block | Divisional Bhavan / H-Block | New Block / NB")
    gpu_capable: bool = Field(False, description="High-GPU compute capable flag")
    is_available: bool = Field(True, description="Maintenance or active availability status")


class RoomUpdate(BaseModel):
    code: Optional[str] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    floor: Optional[str] = None
    block: Optional[str] = None
    gpu_capable: Optional[bool] = None
    is_available: Optional[bool] = None


class RoomResponse(RoomCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    code: str = Field(..., description="Course code e.g. DS, AI(P), SFCDS")
    full_name: str = Field(..., description="Complete subject title")
    dept_id: Optional[int] = Field(1, description="Department ID")
    lecture_hours: int = Field(3, ge=0, le=10, description="Lecture hours per week (L)")
    tutorial_hours: int = Field(0, ge=0, le=5, description="Tutorial hours per week (T)")
    lab_hours: int = Field(0, ge=0, le=10, description="Practical lab hours per week (P)")
    is_lab: bool = Field(False, description="Requires practical lab room")
    gpu_required: bool = Field(False, description="Requires High-GPU lab")
    slot_type: str = Field("L", description="L | T | P | LIBRARY | IIC | SL_EL | OE | CRT | IDP | M_H")
    requires_consecutive: Optional[int] = Field(None, description="2 or 3 period continuous block lock")


class SubjectUpdate(BaseModel):
    code: Optional[str] = None
    full_name: Optional[str] = None
    lecture_hours: Optional[int] = None
    tutorial_hours: Optional[int] = None
    lab_hours: Optional[int] = None
    is_lab: Optional[bool] = None
    gpu_required: Optional[bool] = None
    slot_type: Optional[str] = None
    requires_consecutive: Optional[int] = None


class SubjectResponse(SubjectCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SectionCreate(BaseModel):
    branch_id: int = Field(1, description="Branch ID")
    year_level: int = Field(2, ge=1, le=4, description="Year level: 1, 2, 3, 4")
    label: str = Field("A", description="Section label: A, B, C...")
    name: str = Field("II AIML-A", description="Full section name")
    strength: int = Field(60, ge=1, le=120, description="Student strength")
    academic_year_id: int = Field(1, description="Academic year ID")
    is_active: bool = Field(True, description="Active schedule status")


class SectionUpdate(BaseModel):
    label: Optional[str] = None
    name: Optional[str] = None
    strength: Optional[int] = None
    is_active: Optional[bool] = None


class SectionResponse(SectionCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SectionSubjectMapRequest(BaseModel):
    section_id: int
    subject_id: int
    lecture_faculty_id: Optional[int] = None
    tutorial_faculty_id: Optional[int] = None
    lab_lead_faculty_id: Optional[int] = None
    lab_co_faculty_ids: Optional[List[int]] = Field(default_factory=list)
    lecture_slots_needed: int = 3
    tutorial_slots_needed: int = 0
    lab_slots_needed: int = 0


class SectionSubjectMapResponse(BaseModel):
    id: int
    section_id: int
    subject_id: int
    lecture_faculty_id: Optional[int] = None
    tutorial_faculty_id: Optional[int] = None
    lab_lead_faculty_id: Optional[int] = None
    lab_co_faculty_ids: Optional[List[int]] = None
    lecture_slots_needed: int
    tutorial_slots_needed: int
    lab_slots_needed: int
    total_slots: int

    model_config = ConfigDict(from_attributes=True)


class CSVImportResult(BaseModel):
    success: bool
    imported_count: int
    errors: List[str] = Field(default_factory=list)
    message: str

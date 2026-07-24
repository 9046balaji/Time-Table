from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


class TimetableEntryBase(BaseModel):
    section_id: int
    subject_id: Optional[int] = None
    room_id: Optional[int] = None
    time_slot_id: int
    faculty_ids: Optional[List[int]] = None
    entry_type: str = "L"


class TimetableEntryCreate(TimetableEntryBase):
    timetable_version_id: int


class TimetableEntryUpdate(BaseModel):
    new_time_slot_id: int
    new_room_id: Optional[int] = None


class TimetableGridEntry(BaseModel):
    id: int
    section: str
    day: str
    period: int
    subject: str
    room: str
    faculty: List[Any]
    entry_type: str
    has_clash: bool = False
    clash_reason: Optional[str] = None

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ClashItem(BaseModel):
    clash_type: str = Field(..., json_schema_extra={"example": "ROOM"})
    day: str = Field(..., json_schema_extra={"example": "WED"})
    period: int = Field(..., json_schema_extra={"example": 1})
    room: Optional[str] = Field(None, json_schema_extra={"example": "606"})
    section_a: str = Field(..., json_schema_extra={"example": "II AIML-E"})
    subject_a: str = Field(..., json_schema_extra={"example": "OOPS(P)"})
    section_b: str = Field(..., json_schema_extra={"example": "II CSBS"})
    subject_b: str = Field(..., json_schema_extra={"example": "DS(P)"})
    message: str = Field(..., json_schema_extra={"example": "WED Period-1, Room 606 → II AIML-E: OOPS(P) AND II CSBS: DS(P)"})


class ClashReportResponse(BaseModel):
    version_id: int
    version_label: str
    hard_violations: int
    soft_violations: int
    status: str
    details: List[ClashItem]

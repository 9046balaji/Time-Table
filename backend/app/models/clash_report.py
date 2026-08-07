from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ClashReport(BaseModel):
    __tablename__ = "clash_reports"

    timetable_version_id = Column(Integer, ForeignKey("timetable_versions.id"), nullable=False, index=True)
    clash_type = Column(String(50), nullable=False)  # ROOM, FACULTY, STUDENT_GAP, BREAK_VIOLATION
    day = Column(String(10), nullable=False)
    period_id = Column(Integer, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True, index=True)
    section_a_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    section_b_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    severity = Column(String(20), default="HARD", nullable=False)  # HARD, SOFT
    details = Column(JSON, nullable=True)
    message = Column(Text, nullable=False)

    __table_args__ = (
        Index('idx_clash_reports_version_type', 'timetable_version_id', 'clash_type'),
    )

    timetable_version = relationship("TimetableVersion")
    room = relationship("Room")
    section_a = relationship("Section", foreign_keys=[section_a_id])
    section_b = relationship("Section", foreign_keys=[section_b_id])

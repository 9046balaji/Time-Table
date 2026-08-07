from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class TimetableEntryFaculty(BaseModel):
    __tablename__ = "timetable_entry_faculty"

    timetable_entry_id = Column(Integer, ForeignKey("timetable_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True)
    role_type = Column(String(20), default="LEAD", nullable=False)  # "LEAD", "CO_INSTRUCTOR", "TA"

    __table_args__ = (
        UniqueConstraint('timetable_entry_id', 'faculty_id', name='uq_entry_faculty'),
    )

    timetable_entry = relationship("TimetableEntry", back_populates="faculty_assignments")
    faculty = relationship("Faculty")

from sqlalchemy import Column, String, Text, Integer, Date, Boolean, ForeignKey, JSON, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class TimetableVersion(BaseModel):
    __tablename__ = "timetable_versions"

    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    version_label = Column(String(20), nullable=False, index=True)  # "V5", "AUTO-V6"
    valid_from = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    solver_run_id = Column(Integer, ForeignKey("solver_runs.id"), nullable=True)
    source = Column(String(20), default="MANUAL", nullable=False)  # "MANUAL", "SOLVER", "IMPORTED"
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index('uq_active_version_per_year', 'academic_year_id', unique=True, postgresql_where=(is_current == True)),
    )

    academic_year = relationship("AcademicYear", back_populates="timetable_versions")
    solver_run = relationship("SolverRun", back_populates="timetable_versions")
    entries = relationship("TimetableEntry", back_populates="timetable_version")


class TimetableEntry(BaseModel):
    __tablename__ = "timetable_entries"

    timetable_version_id = Column(Integer, ForeignKey("timetable_versions.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True, index=True)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False, index=True)
    faculty_ids = Column(JSON, nullable=True)  # List[int]: [lead_id, co1_id, co2_id]
    entry_type = Column(String(20), default="L", nullable=False)
    # Values: "L", "T", "P", "LIBRARY", "IIC", "SL_EL", "OE", "CRT", "IDP", "M_H", "PROJECT", "BREAK", "LUNCH"
    is_global_sync = Column(Boolean, default=False, nullable=False)
    span_periods = Column(Integer, default=1, nullable=False)
    raw_subject_text = Column(String(100), nullable=True)
    raw_room_text = Column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint('timetable_version_id', 'section_id', 'time_slot_id', name='uq_entry_section_slot'),
        Index('idx_tt_entries_room_slot', 'timetable_version_id', 'room_id', 'time_slot_id'),
        Index('idx_tt_entries_section_slot', 'timetable_version_id', 'section_id', 'time_slot_id'),
        CheckConstraint("span_periods BETWEEN 1 AND 4", name="chk_span_periods_range"),
    )

    timetable_version = relationship("TimetableVersion", back_populates="entries")
    section = relationship("Section", back_populates="timetable_entries")
    subject = relationship("Subject", back_populates="timetable_entries")
    room = relationship("Room", back_populates="timetable_entries")
    time_slot = relationship("TimeSlot", back_populates="timetable_entries")
    faculty_assignments = relationship("TimetableEntryFaculty", back_populates="timetable_entry", cascade="all, delete-orphan")

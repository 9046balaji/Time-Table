from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Subject(BaseModel):
    __tablename__ = "subjects"

    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    code = Column(String(30), nullable=False, index=True)
    full_name = Column(Text, nullable=False)
    lecture_hours = Column(Integer, default=3, nullable=False)
    tutorial_hours = Column(Integer, default=0, nullable=False)
    lab_hours = Column(Integer, default=0, nullable=False)
    is_lab = Column(Boolean, default=False, nullable=False)
    gpu_required = Column(Boolean, default=False, nullable=False)
    slot_type = Column(String(20), default="L", nullable=False)
    # Values: "L", "T", "P", "LIBRARY", "IIC", "SL_EL", "OE", "CRT", "IDP", "M_H"
    requires_consecutive = Column(Integer, nullable=True)

    department = relationship("Department", back_populates="subjects")
    section_subjects = relationship("SectionSubject", back_populates="subject")
    timetable_entries = relationship("TimetableEntry", back_populates="subject")

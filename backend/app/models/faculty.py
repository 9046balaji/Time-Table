from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Faculty(BaseModel):
    __tablename__ = "faculty"

    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    employee_id = Column(String(30), unique=True, index=True, nullable=True)
    name = Column(Text, nullable=False, index=True)
    designation = Column(String(50), default="Assistant Professor", nullable=False)
    max_hours_per_week = Column(Integer, default=16, nullable=False)
    is_external = Column(Boolean, default=False, nullable=False)
    # availability format: {"MON": [1, 2, 3, 4, 5, 6, 7, 8], "TUE": [...]}
    availability = Column(JSON, nullable=True)

    department = relationship("Department", back_populates="faculty_members", foreign_keys=[dept_id])
    section_subjects_lecture = relationship("SectionSubject", back_populates="lecture_faculty", foreign_keys="SectionSubject.lecture_faculty_id")
    section_subjects_tutorial = relationship("SectionSubject", back_populates="tutorial_faculty", foreign_keys="SectionSubject.tutorial_faculty_id")
    section_subjects_lab_lead = relationship("SectionSubject", back_populates="lab_lead_faculty", foreign_keys="SectionSubject.lab_lead_faculty_id")

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class MultiFacultyAssignment(BaseModel):
    __tablename__ = "multi_faculty_assignments"

    section_subject_id = Column(Integer, ForeignKey("section_subjects.id"), nullable=False)
    primary_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    co_faculty_ids = Column(JSON, nullable=True)  # List of faculty IDs
    role = Column(String(50), default="LAB_CO_INSTRUCTORS", nullable=False)

    section_subject = relationship("SectionSubject")
    primary_faculty = relationship("Faculty", foreign_keys=[primary_faculty_id])

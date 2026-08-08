from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Section(BaseModel):
    __tablename__ = "sections"

    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    year_level = Column(Integer, nullable=False, default=2)  # 1, 2, 3, 4
    label = Column(String(50), nullable=False)  # "A", "B", "C", "II MSC (DS)", etc.
    name = Column(String(50), nullable=False, index=True)  # "II AIML-A"

    strength = Column(Integer, default=60, nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('branch_id', 'year_level', 'label', 'academic_year_id', name='uq_section_branch_year_label'),
    )

    branch = relationship("Branch", back_populates="sections")
    academic_year = relationship("AcademicYear", back_populates="sections")
    section_subjects = relationship("SectionSubject", back_populates="section")
    timetable_entries = relationship("TimetableEntry", back_populates="section")

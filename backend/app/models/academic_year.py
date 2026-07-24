from sqlalchemy import Column, String, Integer, Date, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AcademicYear(BaseModel):
    __tablename__ = "academic_years"

    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    label = Column(String(30), nullable=True)  # e.g., "2026-27 Sem I"
    is_current = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    sections = relationship("Section", back_populates="academic_year")
    timetable_versions = relationship("TimetableVersion", back_populates="academic_year")

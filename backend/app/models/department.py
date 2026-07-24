from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Department(BaseModel):
    __tablename__ = "departments"

    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(Text, nullable=False)
    head_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    program_type = Column(String(50), nullable=True)  # UG, PG, Integrated

    branches = relationship("Branch", back_populates="department")
    faculty_members = relationship("Faculty", back_populates="department", foreign_keys="Faculty.dept_id")
    subjects = relationship("Subject", back_populates="department")
    rooms = relationship("Room", back_populates="department")

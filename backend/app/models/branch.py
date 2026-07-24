from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Branch(BaseModel):
    __tablename__ = "branches"

    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    code = Column(String(20), nullable=False, index=True)
    name = Column(Text, nullable=False)

    department = relationship("Department", back_populates="branches")
    sections = relationship("Section", back_populates="branch")

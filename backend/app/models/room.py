from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Room(BaseModel):
    __tablename__ = "rooms"

    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    room_type = Column(String(30), default="classroom", nullable=False)
    # Values: "classroom", "computer_lab", "gpu_lab", "project_room", "seminar_hall", "external"
    capacity = Column(Integer, default=60, nullable=False)
    floor = Column(String(10), nullable=True)  # "6", "5", "AFTF", "AFF", "NB"
    block = Column(String(30), default="U-Block", nullable=False)
    gpu_capable = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    department = relationship("Department", back_populates="rooms")
    timetable_entries = relationship("TimetableEntry", back_populates="room")

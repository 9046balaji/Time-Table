from sqlalchemy import Column, String, Integer, Time, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class TimeSlot(BaseModel):
    __tablename__ = "time_slots"

    day = Column(String(3), nullable=False, index=True)  # "MON".."SAT"
    period = Column(Integer, nullable=True)  # 1..8, NULL for break/lunch
    slot_label = Column(String(20), nullable=True)  # "P1", "TEA BREAK", "LUNCH"
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint('day', 'period', name='uq_timeslot_day_period'),
    )

    timetable_entries = relationship("TimetableEntry", back_populates="time_slot")

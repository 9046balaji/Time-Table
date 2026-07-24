from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SolverRun(BaseModel):
    __tablename__ = "solver_runs"

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    algorithm = Column(String(50), default="CP-SAT", nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    # status values: "pending", "running", "completed", "failed", "cancelled"
    hard_violations = Column(Integer, default=0, nullable=False)
    soft_violations = Column(Integer, default=0, nullable=False)
    fitness_score = Column(Float, default=0.0, nullable=False)
    generation_count = Column(Integer, default=0, nullable=False)
    runtime_seconds = Column(Float, default=0.0, nullable=False)
    scope_json = Column(JSON, nullable=True)  # Section IDs or Scope string
    config = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    timetable_versions = relationship("TimetableVersion", back_populates="solver_run")

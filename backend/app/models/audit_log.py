from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.sql import func
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False)  # UPDATE_SLOT, RUN_SOLVER, IMPORT_EXCEL
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

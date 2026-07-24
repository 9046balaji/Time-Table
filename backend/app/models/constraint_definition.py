from sqlalchemy import Column, String, Integer, Boolean, Text
from app.models.base import BaseModel


class ConstraintDefinition(BaseModel):
    __tablename__ = "constraint_definitions"

    code = Column(String(20), unique=True, index=True, nullable=False)  # HC-01..HC-10, SC-01..SC-10
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)  # HARD, SOFT
    default_weight = Column(Integer, default=1000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

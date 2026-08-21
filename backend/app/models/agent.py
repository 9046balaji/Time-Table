from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AgentSession(BaseModel):
    __tablename__ = "agent_sessions"

    goal = Column(String(200), nullable=False)
    status = Column(String(30), default="active", nullable=False)
    current_step = Column(String(50), default="observe", nullable=False)
    priority = Column(JSON, default=list, nullable=False)
    summary = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)

    # Added Phase 1 & 10 fields for iteration tracking, approval gate state, and resilience
    iteration = Column(Integer, default=1, nullable=False)
    total_iterations = Column(Integer, default=1, nullable=False)
    approval_required = Column(Boolean, default=False, nullable=False)
    approval_status = Column(String(30), default="none", nullable=False)  # "none", "pending_approval", "approved", "rejected"
    completed_actions = Column(JSON, default=list, nullable=False)
    failed_actions = Column(JSON, default=list, nullable=False)
    session_timeout_at = Column(DateTime, nullable=True)

    events = relationship("AgentEvent", back_populates="session", cascade="all, delete-orphan")
    actions = relationship("AgentAction", back_populates="session", cascade="all, delete-orphan")
    decisions = relationship("AgentDecision", back_populates="session", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="session", cascade="all, delete-orphan")
    runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan")


class AgentEvent(BaseModel):
    __tablename__ = "agent_events"

    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    sequence_number = Column(Integer, default=1, nullable=False)
    event_type = Column(String(50), nullable=False)
    source = Column(String(30), default="system", nullable=False)
    severity = Column(String(20), default="medium", nullable=False)
    room_code = Column(String(50), nullable=True)
    affected_sections = Column(JSON, default=list, nullable=False)
    summary = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)

    session = relationship("AgentSession", back_populates="events")


class AgentAction(BaseModel):
    __tablename__ = "agent_actions"

    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    status = Column(String(30), default="success", nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)

    session = relationship("AgentSession", back_populates="actions")


class AgentDecision(BaseModel):
    __tablename__ = "agent_decisions"

    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    decision_type = Column(String(50), nullable=False)
    reason_code = Column(String(50), nullable=False)
    selected_option = Column(String(100), nullable=False)
    risk_level = Column(String(20), default="low", nullable=False)
    rationale = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)

    session = relationship("AgentSession", back_populates="decisions")


class ApprovalRequest(BaseModel):
    __tablename__ = "approval_requests"

    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    risk_level = Column(String(20), default="medium", nullable=False)
    status = Column(String(30), default="pending_approval", nullable=False)  # "pending_approval", "approved", "rejected"
    candidate_snapshot_id = Column(Integer, nullable=True)
    rationale = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    session = relationship("AgentSession", back_populates="approval_requests")


class AgentRun(BaseModel):
    __tablename__ = "agent_runs"

    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    iteration = Column(Integer, default=1, nullable=False)
    objective_score = Column(Integer, default=0, nullable=False)
    hard_violations_count = Column(Integer, default=0, nullable=False)
    soft_penalty_total = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="completed", nullable=False)

    session = relationship("AgentSession", back_populates="runs")

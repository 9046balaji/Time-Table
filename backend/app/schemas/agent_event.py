from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field


class AgentEventMessage(BaseModel):
    """Strict schema for real-time WebSocket event broadcasts."""
    type: Literal["perception", "consensus", "approval", "progress", "decision", "error"]
    session_id: int
    step: str
    message: str
    timestamp: float
    payload: Dict[str, Any] = Field(default_factory=dict)


class PerceptionPayload(BaseModel):
    incident_id: int
    scenario_type: str
    target_code: Optional[str] = None
    affected_sections: List[str] = Field(default_factory=list)
    severity: str = "medium"


class ConsensusPayload(BaseModel):
    consensus_passed: bool
    final_decision: str
    total_votes: int
    approve_votes: int
    reject_votes: int
    sub_agent_votes: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalPayload(BaseModel):
    approval_request_id: Optional[int] = None
    risk_level: str
    status: str
    rationale: str

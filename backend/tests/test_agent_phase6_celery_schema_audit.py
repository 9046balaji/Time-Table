import pytest
import sys, os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.agent_event import AgentEventMessage, PerceptionPayload, ConsensusPayload, ApprovalPayload


def test_phase6_typed_websocket_schemas():
    msg = AgentEventMessage(
        type="perception",
        session_id=1,
        step="observe",
        message="Emergency disruption incident logged",
        timestamp=time.time(),
        payload={"incident_id": 101, "scenario_type": "room_failure"}
    )
    assert msg.type == "perception"
    assert msg.session_id == 1

    c_payload = ConsensusPayload(
        consensus_passed=True,
        final_decision="APPROVED",
        total_votes=3,
        approve_votes=3,
        reject_votes=0,
        sub_agent_votes=[]
    )
    assert c_payload.consensus_passed is True

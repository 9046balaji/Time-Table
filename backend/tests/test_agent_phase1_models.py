import pytest
from sqlalchemy import select
from app.core.database import ensure_database, AsyncSessionLocal
from app.models.agent import AgentSession, ApprovalRequest, AgentRun


@pytest.mark.asyncio
async def test_phase1_agent_models_and_approval_requests():
    await ensure_database()
    async with AsyncSessionLocal() as db:
        # Create session
        session = AgentSession(
            goal="Test Phase 1 models",
            status="active",
            current_step="observe",
            iteration=2,
            total_iterations=3,
            approval_required=True,
            approval_status="pending_approval"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        assert session.id is not None
        assert session.iteration == 2
        assert session.approval_required is True

        # Create approval request
        app_req = ApprovalRequest(
            session_id=session.id,
            risk_level="high",
            status="pending_approval",
            rationale="Room 604 offline, local repair requires human confirmation"
        )
        db.add(app_req)

        # Create agent run
        agent_run = AgentRun(
            session_id=session.id,
            iteration=1,
            objective_score=95,
            hard_violations_count=0,
            soft_penalty_total=50,
            status="completed"
        )
        db.add(agent_run)

        await db.commit()
        await db.refresh(app_req)
        await db.refresh(agent_run)

        assert app_req.id is not None
        assert app_req.status == "pending_approval"
        assert agent_run.id is not None
        assert agent_run.objective_score == 95

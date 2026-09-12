from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.agent_service import AgentService

router = APIRouter()


@router.post("/sessions", response_model=Dict[str, Any])
async def create_agent_session(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    goal = str(payload.get("goal") or "Repair timetable automatically").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")
    priority = payload.get("priority") or []
    if not isinstance(priority, list):
        raise HTTPException(status_code=400, detail="priority must be a list")
    return await AgentService.create_session(db, goal=goal, priority=[str(p) for p in priority])


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_agent_session(session_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await AgentService.get_session(db, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


_last_simulation_times: Dict[int, float] = {}

@router.get("/health/data-integrity", response_model=Dict[str, Any])
async def get_data_integrity_health(
    version_id: Optional[int] = Query(None, description="Optional version ID to inspect"),
    db: AsyncSession = Depends(get_db)
):
    """Health check endpoint auditing raw text fields vs FK database relations."""
    from app.services.timetable_service import TimetableService
    return await TimetableService.check_data_integrity(db, version_id=version_id)

@router.post("/simulate-room-failure", response_model=Dict[str, Any])
async def simulate_room_failure(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    session_id = payload.get("session_id")
    room_code = str(payload.get("room_code") or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not room_code:
        raise HTTPException(status_code=400, detail="room_code is required")

    import time
    s_id = int(session_id)
    now = time.time()
    if s_id in _last_simulation_times and (now - _last_simulation_times[s_id]) < 1.0:
        raise HTTPException(status_code=429, detail="Simulation cooldown active. Please wait 1 second before triggering consecutive disruptions.")
    _last_simulation_times[s_id] = now

    try:
        return await AgentService.simulate_room_failure(
            db,
            session_id=s_id,
            room_code=room_code,
            severity=str(payload.get("severity") or "high"),
            affected_sections=payload.get("affected_sections") or [],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/repair-suggestion", response_model=Dict[str, Any])
async def create_repair_suggestion(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    room_code = str(payload.get("room_code") or "").strip()
    if not room_code:
        raise HTTPException(status_code=400, detail="room_code is required")

    try:
        return await AgentService.create_repair_suggestion(
            db,
            session_id=session_id,
            room_code=room_code,
            affected_sections=payload.get("affected_sections") or [],
            proposed_room=str(payload.get("proposed_room") or "nearest_available_lab").strip(),
            risk_level=str(payload.get("risk_level") or "medium"),
            reason=str(payload.get("reason") or "Local repair recommended"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/repair-decision", response_model=Dict[str, Any])
async def resolve_repair_decision(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    decision = str(payload.get("decision") or "").strip()
    rationale = payload.get("rationale")
    if not decision:
        raise HTTPException(status_code=400, detail="decision is required")

    try:
        return await AgentService.resolve_repair_decision(
            db,
            session_id=session_id,
            decision=decision,
            rationale=str(rationale) if rationale is not None else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/approve", response_model=Dict[str, Any])
async def approve_repair_request(
    session_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    rationale = (payload or {}).get("rationale") or "Human administrator approved local repair plan."
    try:
        return await AgentService.resolve_repair_decision(
            db,
            session_id=session_id,
            decision="approved",
            rationale=rationale,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/reject", response_model=Dict[str, Any])
async def reject_repair_request(
    session_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    rationale = (payload or {}).get("rationale") or "Human administrator rejected local repair plan."
    try:
        return await AgentService.resolve_repair_decision(
            db,
            session_id=session_id,
            decision="rejected",
            rationale=rationale,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/parse-command", response_model=Dict[str, Any])
async def parse_natural_command(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    command_text = str(payload.get("command") or payload.get("text") or "").strip()
    if not command_text:
        raise HTTPException(status_code=400, detail="command or text is required")
    try:
        return await AgentService.parse_natural_command(db, session_id=session_id, command_text=command_text)
    except ValueError as exc:
        # An uninterpretable directive is a bad request, not a missing session.
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message) from exc


@router.post("/sessions/{session_id}/repair-validation", response_model=Dict[str, Any])
async def validate_repair(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    room_code = str(payload.get("room_code") or "").strip()
    if not room_code:
        raise HTTPException(status_code=400, detail="room_code is required")

    try:
        return await AgentService.validate_repair(
            db,
            session_id=session_id,
            room_code=room_code,
            affected_sections=payload.get("affected_sections") or [],
            check_type=str(payload.get("check_type") or "room_capacity_and_conflict"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/observe", response_model=Dict[str, Any])
async def observe_agent_state(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await AgentService.observe_state(db, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/rollback", response_model=Dict[str, Any])
async def rollback_agent_schedule(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await AgentService.rollback(db, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/publish", response_model=Dict[str, Any])
async def publish_agent_schedule(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Publish the session's validated candidate as a new timetable version."""
    version_label = str(payload.get("version_label") or "").strip()
    if not version_label:
        raise HTTPException(status_code=400, detail="version_label is required")

    from app.services.tool_registry import ToolRegistry
    from app.models.agent import AgentSession
    from sqlalchemy import select as _select

    session = (await db.execute(
        _select(AgentSession).where(AgentSession.id == session_id)
    )).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    entries = payload.get("entries") or (session.context or {}).get("candidate_entries") or []
    if not entries:
        raise HTTPException(
            status_code=400,
            detail="No candidate schedule to publish. Run a repair first.",
        )
    try:
        return await ToolRegistry.publish_schedule(
            db,
            session_id=session_id,
            entries=entries,
            version_label=version_label,
            notes=str(payload.get("notes") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/assign-faculty", response_model=Dict[str, Any])
async def assign_faculty(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Assign instructors to one timetable entry, refusing double-bookings."""
    entry_id = payload.get("entry_id")
    faculty_ids = payload.get("faculty_ids") or []
    if not entry_id or not faculty_ids:
        raise HTTPException(status_code=400, detail="entry_id and faculty_ids are required")

    from app.services.tool_registry import ToolRegistry
    try:
        return await ToolRegistry.assign_faculty_to_entry(
            db, session_id=session_id, entry_id=int(entry_id),
            faculty_ids=[int(f) for f in faculty_ids],
        )
    except ValueError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message) from exc


@router.post("/sessions/{session_id}/create-entry", response_model=Dict[str, Any])
async def create_entry(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Create a new class slot, refusing any placement that clashes."""
    required = ["section", "subject", "day", "period", "room"]
    missing = [k for k in required if not payload.get(k)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required field(s): {missing}")

    from app.services.tool_registry import ToolRegistry
    try:
        return await ToolRegistry.create_timetable_entry(
            db,
            session_id=session_id,
            section=str(payload["section"]),
            subject=str(payload["subject"]),
            day=str(payload["day"]),
            period=int(payload["period"]),
            room=str(payload["room"]),
            entry_type=str(payload.get("entry_type") or "L"),
            faculty_ids=[int(f) for f in (payload.get("faculty_ids") or [])],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/delete-entry", response_model=Dict[str, Any])
async def delete_entry(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Delete a timetable entry, safely releasing the slot with audit trace."""
    entry_id = payload.get("entry_id")
    if not entry_id:
        raise HTTPException(status_code=400, detail="entry_id is required")

    from app.services.tool_registry import ToolRegistry
    try:
        return await ToolRegistry.delete_timetable_entry(
            db,
            session_id=session_id,
            entry_id=int(entry_id),
            reason=str(payload.get("reason") or "agent_cancel_slot"),
        )
    except ValueError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message) from exc


@router.post("/simulate/{scenario_type}", response_model=Dict[str, Any])
async def simulate_disruption_scenario(
    scenario_type: str,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    import time
    s_id = int(session_id)
    now = time.time()
    if s_id in _last_simulation_times and (now - _last_simulation_times[s_id]) < 1.0:
        raise HTTPException(status_code=429, detail="Simulation cooldown active. Please wait 1 second before triggering consecutive disruptions.")
    _last_simulation_times[s_id] = now

    from app.services.mission_simulator import MissionSimulator
    try:
        return await MissionSimulator.trigger_scenario(
            db,
            session_id=int(session_id),
            scenario_type=scenario_type,
            target_code=payload.get("target_code"),
            affected_sections=payload.get("affected_sections") or [],
            payload_extra=payload.get("extra") or {}
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.websocket("/stream/{session_id}")
async def stream_agent_events(websocket: WebSocket, session_id: int):
    from app.services.agent_websocket_manager import agent_ws_manager
    await agent_ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive & listen for client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        agent_ws_manager.disconnect(session_id, websocket)
    except Exception:
        agent_ws_manager.disconnect(session_id, websocket)


@router.post("/sessions/{session_id}/consensus", response_model=Dict[str, Any])
async def evaluate_multi_agent_consensus(
    session_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    entries = payload.get("entries") or []
    from app.services.multi_agent_consensus import MultiAgentConsensusEngine
    try:
        return await MultiAgentConsensusEngine.evaluate_consensus(
            db,
            session_id=session_id,
            timetable_entries=entries
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/multi-agent/synthesize", response_model=Dict[str, Any])
async def run_multi_agent_synthesis(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Trigger collaborative multi-agent timetable synthesis across all 7 specialized agents."""
    version_id = int(payload.get("version_id", 12))
    rounds = int(payload.get("max_rounds", 5))
    scope = str(payload.get("scope", "ALL"))
    target_sections = payload.get("target_sections") or []
    user_directive = payload.get("user_directive")
    session_id = payload.get("session_id")

    from app.services.multi_agent_scheduler import MasterArbiterAgent
    arbiter = MasterArbiterAgent(db=db, session_id=session_id)
    return await arbiter.execute_collaborative_synthesis(
        target_version_id=version_id,
        max_negotiation_rounds=rounds,
        scope=scope,
        target_sections=target_sections,
        user_directive=user_directive
    )


@router.get("/multi-agent/sections", response_model=Dict[str, Any])
async def get_multi_agent_sections(
    version_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Returns unique academic sections and branches for targeted agent scheduling."""
    from app.services.timetable_service import TimetableService
    vid = version_id or 12
    tt = await TimetableService.get_version_timetable(db, version_id=vid, section_name="ALL")
    slots = tt.get("entries", [])
    sections_set = set()
    for s in slots:
        sec = str(s.get("section") or s.get("sectionName") or "").strip()
        if sec:
            sections_set.add(sec)

    sorted_secs = sorted(list(sections_set))
    y2 = [s for s in sorted_secs if "II " in s]
    y3 = [s for s in sorted_secs if "III " in s]
    y4 = [s for s in sorted_secs if "IV " in s]
    others = [s for s in sorted_secs if s not in y2 and s not in y3 and s not in y4]

    return {
        "version_id": vid,
        "total_sections": len(sorted_secs),
        "all_sections": sorted_secs,
        "by_year": {
            "II_YEAR": y2,
            "III_YEAR": y3,
            "IV_YEAR": y4,
            "OTHER": others
        }
    }


@router.get("/multi-agent/audit", response_model=Dict[str, Any])
async def run_multi_agent_audit(
    version_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Instant 7-agent audit across curriculum, faculty, venue/blocks, temporal flow, student welfare, lab infra, and validator."""
    from app.services.timetable_service import TimetableService
    from app.services.multi_agent_scheduler import (
        SectionCurriculumAgent, FacultyWorkloadAgent, VenueBlockAgent, TemporalFlowAgent,
        StudentWelfareAgent, LabTechInfraAgent
    )
    from backend.solver.conflict_checker import ConflictChecker
    vid = version_id or 12
    tt = await TimetableService.get_version_timetable(db, version_id=vid, section_name="ALL")
    slots = tt.get("entries", [])

    vote_c = SectionCurriculumAgent.cast_vote(slots)
    vote_f = FacultyWorkloadAgent.cast_vote(slots)
    vote_v = VenueBlockAgent.cast_vote(slots)
    vote_t = TemporalFlowAgent.cast_vote(slots)
    vote_w = StudentWelfareAgent.cast_vote(slots)
    vote_i = LabTechInfraAgent.cast_vote(slots)

    checker = ConflictChecker()
    rep = checker.detect(slots)
    val_approved = (rep.total_hard_violations == 0)
    vote_val = {
        "agent": "ValidatorAgent",
        "vote": "APPROVE" if val_approved else "REJECT",
        "violations": rep.total_hard_violations,
        "has_veto_power": True,
        "rationale": "Ground truth verified: 0 hard clashes." if val_approved else f"VETO: {rep.total_hard_violations} hard clashes detected.",
        "metrics": {"room_clashes": rep.room_clashes, "faculty_clashes": rep.faculty_clashes, "student_clashes": rep.student_clashes}
    }

    votes = [
        {"agent": vote_c.agent_name, "vote": vote_c.vote, "violations": vote_c.violations_detected, "rationale": vote_c.rationale, "metrics": vote_c.metrics},
        {"agent": vote_f.agent_name, "vote": vote_f.vote, "violations": vote_f.violations_detected, "rationale": vote_f.rationale, "metrics": vote_f.metrics},
        {"agent": vote_v.agent_name, "vote": vote_v.vote, "violations": vote_v.violations_detected, "rationale": vote_v.rationale, "metrics": vote_v.metrics},
        {"agent": vote_t.agent_name, "vote": vote_t.vote, "violations": vote_t.violations_detected, "rationale": vote_t.rationale, "metrics": vote_t.metrics},
        {"agent": vote_w.agent_name, "vote": vote_w.vote, "violations": vote_w.violations_detected, "rationale": vote_w.rationale, "metrics": vote_w.metrics},
        {"agent": vote_i.agent_name, "vote": vote_i.vote, "violations": vote_i.violations_detected, "rationale": vote_i.rationale, "metrics": vote_i.metrics},
        vote_val
    ]
    unanimous = all(v["vote"] == "APPROVE" for v in votes)
    return {
        "version_id": vid,
        "total_slots": len(slots),
        "unanimous": unanimous,
        "status": "APPROVED" if unanimous else "REJECTED",
        "votes": votes
    }


@router.post("/multi-agent/publish", response_model=Dict[str, Any])
async def publish_multi_agent_timetable(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Commit approved multi-agent schedule as a new official TimetableVersion."""
    from app.services.write_tools import publish_schedule
    label = str(payload.get("version_label") or "AUTO-V6")
    entries = payload.get("entries") or []
    if not entries:
        raise HTTPException(status_code=400, detail="No entries provided to publish")
    return await publish_schedule(
        db=db,
        session_id=payload.get("session_id", 1),
        entries=entries,
        version_label=label,
        notes=payload.get("notes", "Published by Autonomous 7-Agent Society")
    )


# =====================================================================
# NEXT-GEN AGENT EXTENSIONS: SUBSTITUTE, EXAMS, PARETO, TELEMETRY, V2
# =====================================================================

@router.post("/substitute/find-candidates", response_model=Dict[str, Any])
async def find_substitute_candidates(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Identifies and ranks eligible substitute faculty adhering to AICTE hours and daily fatigue limits."""
    faculty_name = str(payload.get("faculty_name") or "").strip()
    if not faculty_name:
        raise HTTPException(status_code=400, detail="faculty_name is required")

    from app.services.substitute_dispatcher import SubstituteDispatcher
    return await SubstituteDispatcher.find_candidate_substitutes(
        db=db,
        faculty_name=faculty_name,
        day=payload.get("day"),
        period=payload.get("period"),
        subject_code=payload.get("subject"),
        version_id=int(payload.get("version_id", 5))
    )


@router.post("/substitute/dispatch", response_model=Dict[str, Any])
async def dispatch_substitute_faculty(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Executes safe substitute assignment with pre-snapshot rollback guard and ground-truth validation."""
    entry_id = payload.get("entry_id")
    substitute_id = payload.get("substitute_faculty_id")
    session_id = payload.get("session_id", 1)

    if not entry_id or not substitute_id:
        raise HTTPException(status_code=400, detail="entry_id and substitute_faculty_id are required")

    from app.services.substitute_dispatcher import SubstituteDispatcher
    try:
        return await SubstituteDispatcher.dispatch_substitute(
            db=db,
            session_id=int(session_id),
            entry_id=int(entry_id),
            substitute_faculty_id=int(substitute_id),
            original_faculty_name=payload.get("original_faculty_name"),
            reason=str(payload.get("reason") or "Emergency absence reassignment")
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/exam/generate", response_model=Dict[str, Any])
async def generate_exam_schedule(
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    p = payload or {}
    from app.services.exam_scheduler_agent import ExamSchedulerAgent
    return await ExamSchedulerAgent.generate_exam_schedule(
        db=db,
        exam_type=str(p.get("exam_type", "MID_TERM_1")),
        start_date=str(p.get("start_date", "2026-10-12")),
        num_days=int(p.get("num_days", 6)),
        spacing_factor=float(p.get("spacing_factor", 0.5)),
        target_sections=p.get("target_sections") or p.get("sections")
    )


@router.post("/pareto/evaluate", response_model=Dict[str, Any])
async def evaluate_pareto_frontier(
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Evaluates multi-objective Pareto trade-offs across Faculty, Student, and Infrastructure profiles."""
    p = payload or {}
    from app.services.pareto_optimizer import ParetoOptimizer
    return await ParetoOptimizer.evaluate_timetable(
        db=db,
        version_id=int(p.get("version_id", 5)),
        candidate_entries=p.get("entries")
    )


@router.post("/telemetry/occupancy", response_model=Dict[str, Any])
async def record_room_telemetry(payload: Dict[str, Any]):
    """Ingests live IoT room occupancy from campus edge cameras or BLE beacons."""
    room_code = str(payload.get("room_code") or "").strip()
    if not room_code:
        raise HTTPException(status_code=400, detail="room_code is required")
    headcount = int(payload.get("detected_headcount", 0))

    from app.services.room_telemetry_agent import RoomTelemetryAgent
    return RoomTelemetryAgent.record_sensor_telemetry(
        room_code=room_code,
        detected_headcount=headcount,
        sensor_type=str(payload.get("sensor_type", "EDGE_VISION_CAMERA")),
        confidence=float(payload.get("confidence", 0.95))
    )


@router.get("/telemetry/audit", response_model=Dict[str, Any])
async def audit_room_telemetry(
    day: str = Query("MON"),
    period: int = Query(3),
    version_id: int = Query(5),
    db: AsyncSession = Depends(get_db)
):
    """Audits scheduled classroom occupancy against edge sensor readings to detect ghost bookings."""
    from app.services.room_telemetry_agent import RoomTelemetryAgent
    return await RoomTelemetryAgent.audit_room_utilization(
        db=db,
        day=day,
        period=period,
        version_id=version_id
    )


@router.post("/telemetry/reclaim", response_model=Dict[str, Any])
async def reclaim_ghost_room(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Reclaims vacant ghost-booked room for tutorial or remedial sessions with audit logging."""
    room_code = str(payload.get("room_code") or "").strip()
    if not room_code:
        raise HTTPException(status_code=400, detail="room_code is required")

    from app.services.room_telemetry_agent import RoomTelemetryAgent
    return await RoomTelemetryAgent.reclaim_ghost_room(
        db=db,
        session_id=int(payload.get("session_id", 1)),
        room_code=room_code,
        day=str(payload.get("day", "MON")),
        period=int(payload.get("period", 3)),
        purpose=str(payload.get("purpose", "Ad-hoc remedial session"))
    )


@router.post("/hierarchical/solve", response_model=Dict[str, Any])
async def solve_hierarchically(
    payload: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Triggers V2 Hierarchical Domain Decomposition (Phase 1 Macro Locks -> Phase 2 Parallel Micro-Solvers)."""
    p = payload or {}
    from app.solver.hierarchical_decomposer import HierarchicalDecomposer
    return await HierarchicalDecomposer.solve_hierarchically(
        db=db,
        version_id=int(p.get("version_id", 5)),
        timeout_seconds=int(p.get("timeout_seconds", 30))
    )


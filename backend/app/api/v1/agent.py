from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
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
async def get_data_integrity_health(db: AsyncSession = Depends(get_db)):
    """Health check endpoint auditing raw text fields vs FK database relations."""
    from app.services.timetable_service import TimetableService
    return await TimetableService.check_data_integrity(db)

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

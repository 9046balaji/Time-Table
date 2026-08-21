from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
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

    try:
        return await AgentService.simulate_room_failure(
            db,
            session_id=int(session_id),
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

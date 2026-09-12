import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import ensure_database
from app.models.agent import AgentSession, AgentEvent
from app.services.tool_registry import ToolRegistry
from app.services.agent_service import AgentService


class MissionSimulator:
    """
    Event-Driven Campus Disruption Simulator Engine.
    Simulates real-world academic disruptions (room failures, GPU lab outages, faculty absences, capacity surges, new class additions, constraint modifications)
    and automatically triggers the Agent's perception-plan-repair loop.
    """

    SCENARIOS = {
        "room_failure": "ROOM_UNAVAILABLE",
        "gpu_lab_failure": "GPU_LAB_UNAVAILABLE",
        "faculty_absence": "FACULTY_UNAVAILABLE",
        "capacity_surge": "CAPACITY_SURGE",
        "new_class_addition": "NEW_CLASS_ADDED",
        "priority_reroute": "PRIORITY_REROUTE",
        "constraint_adjustment": "CONSTRAINT_ADJUSTMENT",
        "constraint_modification": "CONSTRAINT_MODIFICATION",
    }

    @staticmethod
    async def trigger_scenario(
        db: AsyncSession,
        session_id: int,
        scenario_type: str,
        target_code: Optional[str] = None,
        affected_sections: Optional[List[str]] = None,
        payload_extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a targeted disruption scenario, logs the incident event,
        invokes local repair recommendation, and updates session context.
        """
        await ensure_database()
        res = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = res.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        scenario = str(scenario_type or "").strip().lower()
        event_type = MissionSimulator.SCENARIOS.get(scenario, "DISRUPTION_EVENT")
        sections = list(affected_sections or [])
        extra = payload_extra or {}

        if scenario == "room_failure":
            room_code = str(target_code or "604").strip()
            summary = f"Emergency maintenance triggered for Room {room_code}. Impacted sections: {', '.join(sections) or 'All assigned'}."
            severity = "high"
            code_key = room_code
        elif scenario == "gpu_lab_failure":
            room_code = str(target_code or "AFTF-12").strip()
            summary = f"M7 GPU High-Performance Lab {room_code} hardware outage. Re-routing AI/DL lab sessions to alternate GPU block."
            severity = "high"
            code_key = room_code
        elif scenario == "faculty_absence":
            fac_name = str(target_code or "Dr. S. Srikantha Reddy").strip()
            summary = f"Faculty member {fac_name} reported unavailable. Re-allocating assigned slots."
            severity = "high"
            code_key = fac_name
        elif scenario == "capacity_surge":
            room_code = str(target_code or "601").strip()
            new_capacity = extra.get("new_student_count", 95)
            summary = f"Section enrollment surge detected for Room {room_code} (student count: {new_capacity}). Capacity audit required."
            severity = "medium"
            code_key = room_code
        elif scenario == "new_class_addition":
            sec_name = str(target_code or "II CSBS-B").strip()
            summary = f"M6 Mid-semester new class section {sec_name} added. Seeking available classroom and faculty slots."
            severity = "medium"
            code_key = sec_name
        elif scenario == "priority_reroute":
            target_sec = str(target_code or "IV AIML-A").strip()
            summary = f"Priority boost granted for cohort {target_sec}. Morning slot preference re-aligned."
            severity = "low"
            code_key = target_sec
        elif scenario in ("constraint_adjustment", "constraint_modification"):
            rule_name = str(target_code or "HC-08").strip()
            summary = f"Global constraint rule {rule_name} modification enforced."
            severity = "medium"
            code_key = rule_name
        else:
            summary = f"Custom disruption event triggered: {scenario}"
            severity = "medium"
            code_key = str(target_code or "GENERIC")

        # 1. Log Disruption Incident Event
        event = AgentEvent(
            session_id=session.id,
            event_type=event_type,
            source="mission_simulator",
            severity=severity,
            room_code=code_key if "room" in scenario or "lab" in scenario or scenario == "capacity_surge" else None,
            affected_sections=sections,
            summary=summary,
            payload={
                "scenario_type": scenario,
                "target_code": code_key,
                "affected_sections": sections,
                **extra
            }
        )
        db.add(event)

        # 2. Trigger Autonomous Local Repair Recommendation
        repair_res = await ToolRegistry.run_local_repair(
            db,
            session_id=session_id,
            room_code=code_key if "room" in scenario or "lab" in scenario else None,
            faculty_name=code_key if scenario == "faculty_absence" else None,
            affected_sections=sections
        )

        session.iteration = (session.iteration or 1) + 1
        session.total_iterations = max(session.total_iterations or 1, session.iteration)
        session.current_step = "plan"
        session.status = "active"
        session.summary = f"{summary} Local repair ready (moved slots: {repair_res['moved_count']}, stability: {repair_res['stability_score']}%)."
        session.context = {
            **(session.context or {}),
            "active_disruption": {
                "scenario": scenario,
                "target": code_key,
                "affected_sections": sections,
                "severity": severity
            },
            "candidate_entries": repair_res.get("entries", []),
            "repair_metrics": {
                "moved_count": repair_res["moved_count"],
                "displaced_sections": repair_res["displaced_sections"],
                "displaced_faculty": repair_res["displaced_faculty"],
                "stability_score": repair_res["stability_score"],
                "risk_level": repair_res["risk_level"]
            }
        }
        await db.commit()
        await db.refresh(event)

        # Broadcast live event via WebSocket manager
        try:
            from app.services.agent_websocket_manager import agent_ws_manager
            await agent_ws_manager.broadcast_event(session_id, {
                "type": "AGENT_EVENT",
                "event_id": event.id,
                "event_type": event_type,
                "summary": summary,
                "severity": severity,
                "target": code_key,
                "repair": {
                    "moved_count": repair_res["moved_count"],
                    "displaced_sections": repair_res["displaced_sections"],
                    "stability_score": repair_res["stability_score"],
                    "risk_level": repair_res["risk_level"]
                }
            })
        except Exception as ws_err:
            print(f"[WebSocket Broadcast Warning] {ws_err}")

        return {
            "incident_id": event.id,
            "session_id": session_id,
            "iteration": session.iteration,
            "scenario": scenario,
            "event_type": event_type,
            "severity": severity,
            "target": code_key,
            "summary": summary,
            "repair_recommendation": {
                "status": repair_res["status"],
                "moved_count": repair_res["moved_count"],
                "displaced_sections": repair_res["displaced_sections"],
                "stability_score": repair_res["stability_score"],
                "risk_level": repair_res["risk_level"],
                "hard_violations": repair_res.get("hard_violations", 0),
                "entries": repair_res.get("entries", [])
            }
        }

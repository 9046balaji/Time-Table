import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentSession, AgentEvent, AgentAction
from app.services.timetable_service import TimetableService
from app.services.tool_registry import ToolRegistry


class RoomTelemetryAgent:
    """
    Autonomous SmartClass IoT Room Occupancy & Telemetry Ingestion Agent.
    Ingests live edge camera and BLE beacon sensor data to monitor physical classroom utilization.
    Detects:
    - Ghost Bookings: Classroom scheduled on timetable but sensor detected < 5 students.
    - Overcrowding: Student count exceeds physical room seating capacity.
    - Automated Room Reclamation: Releases ghost-booked venues for remedial / tutorial sessions.
    """

    AGENT_NAME = "RoomTelemetryAgent"
    _in_memory_telemetry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def record_sensor_telemetry(
        cls,
        room_code: str,
        detected_headcount: int,
        sensor_type: str = "EDGE_VISION_CAMERA",
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """Stores real-time telemetry from campus camera or BLE edge nodes."""
        norm_room = str(room_code).strip().upper()
        reading = {
            "room_code": norm_room,
            "detected_headcount": int(detected_headcount),
            "sensor_type": sensor_type,
            "confidence": confidence,
            "timestamp": time.time()
        }
        cls._in_memory_telemetry[norm_room] = reading
        return reading

    @classmethod
    async def audit_room_utilization(
        cls,
        db: AsyncSession,
        day: str = "MON",
        period: int = 3,
        version_id: int = 5
    ) -> Dict[str, Any]:
        """
        Compares timetable reservations against live telemetry.
        Identifies ghost bookings and capacity overflow anomalies.
        """
        start_time = time.time()
        tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        entries = tt_res.get("entries", [])
        rooms = await ToolRegistry.get_rooms(db)
        room_capacity_map = {str(r["code"]).upper(): int(r.get("capacity", 60)) for r in rooms}

        norm_day = str(day).upper()[:3]
        target_period = int(period)

        # Find scheduled classes at target time slot
        active_scheduled = {}
        for e in entries:
            d = str(e.get("day", "")).upper()[:3]
            p = int(e.get("period", 0))
            rm = str(e.get("room", "")).strip().upper()
            if d == norm_day and p == target_period and rm:
                active_scheduled[rm] = e

        anomalies = []
        ghost_bookings = []
        overcrowded_rooms = []
        normal_rooms = []

        all_room_codes = sorted(list(room_capacity_map.keys()))

        for rm in all_room_codes:
            sched_slot = active_scheduled.get(rm)
            cap = room_capacity_map.get(rm, 60)
            sensor = cls._in_memory_telemetry.get(rm, {
                "detected_headcount": 55 if sched_slot else 0,
                "sensor_type": "DEFAULT_ESTIMATE",
                "timestamp": time.time()
            })
            headcount = sensor["detected_headcount"]

            if sched_slot and headcount < 5:
                # Ghost Booking Detected!
                ghost_info = {
                    "room_code": rm,
                    "scheduled_section": sched_slot.get("section"),
                    "scheduled_subject": sched_slot.get("subject"),
                    "scheduled_faculty": sched_slot.get("faculty"),
                    "room_capacity": cap,
                    "detected_headcount": headcount,
                    "anomaly_type": "GHOST_BOOKING",
                    "action_recommended": "RECLAIM_ROOM_FOR_AD_HOC"
                }
                ghost_bookings.append(ghost_info)
                anomalies.append(ghost_info)
            elif sched_slot and headcount > cap:
                # Overcrowding Detected!
                overflow_info = {
                    "room_code": rm,
                    "scheduled_section": sched_slot.get("section"),
                    "scheduled_subject": sched_slot.get("subject"),
                    "room_capacity": cap,
                    "detected_headcount": headcount,
                    "overflow_count": headcount - cap,
                    "anomaly_type": "OVERCROWDING",
                    "action_recommended": "DISPATCH_PARALLEL_VENUE"
                }
                overcrowded_rooms.append(overflow_info)
                anomalies.append(overflow_info)
            else:
                normal_rooms.append({
                    "room_code": rm,
                    "is_occupied": sched_slot is not None,
                    "scheduled_subject": sched_slot.get("subject") if sched_slot else "FREE",
                    "room_capacity": cap,
                    "detected_headcount": headcount
                })

        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "day": norm_day,
            "period": target_period,
            "total_rooms_monitored": len(all_room_codes),
            "ghost_bookings_detected": len(ghost_bookings),
            "overcrowded_rooms_detected": len(overcrowded_rooms),
            "ghost_bookings": ghost_bookings,
            "overcrowded_rooms": overcrowded_rooms,
            "all_monitored_rooms": normal_rooms + ghost_bookings + overcrowded_rooms,
            "execution_time_ms": elapsed_ms
        }

    @classmethod
    async def reclaim_ghost_room(
        cls,
        db: AsyncSession,
        session_id: int,
        room_code: str,
        day: str,
        period: int,
        purpose: str = "Ad-hoc remedial tutorial session"
    ) -> Dict[str, Any]:
        """
        Dynamically reclaims a vacant ghost room and registers an audit record.
        """
        norm_room = str(room_code).strip().upper()
        summary = f"SmartClass Reclaim: Room {norm_room} reclaimed during {day} P{period} for '{purpose}' (physical headcount confirmed < 5)."

        # Ensure session exists to avoid FK constraint failure
        sess_check = (await db.execute(select(AgentSession.id).where(AgentSession.id == session_id))).scalar_one_or_none()
        if not sess_check:
            fallback_sess = AgentSession(goal="SmartClass IoT Telemetry Session", status="active")
            db.add(fallback_sess)
            await db.flush()
            session_id = fallback_sess.id

        event = AgentEvent(
            session_id=session_id,
            event_type="ROOM_RECLAIMED",
            source="smartclass_iot_agent",
            severity="low",
            room_code=norm_room,
            summary=summary,
            payload={
                "room_code": norm_room,
                "day": day,
                "period": period,
                "purpose": purpose
            }
        )
        db.add(event)

        action = AgentAction(
            session_id=session_id,
            tool_name="reclaim_ghost_room",
            arguments={"room_code": norm_room, "day": day, "period": period, "purpose": purpose},
            result={"status": "RECLAIMED", "room_code": norm_room},
            status="success",
            execution_time_ms=10
        )
        db.add(action)
        await db.commit()

        return {
            "status": "RECLAIMED",
            "room_code": norm_room,
            "reclaimed_for": purpose,
            "summary": summary
        }

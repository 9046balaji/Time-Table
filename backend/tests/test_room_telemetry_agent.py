import pytest
from app.services.room_telemetry_agent import RoomTelemetryAgent


@pytest.mark.asyncio
async def test_room_telemetry_ingestion_and_audit(async_db_session):
    # 1. Ingest normal reading
    read1 = RoomTelemetryAgent.record_sensor_telemetry(
        room_code="601",
        detected_headcount=58,
        sensor_type="EDGE_VISION_CAMERA"
    )
    assert read1["room_code"] == "601"
    assert read1["detected_headcount"] == 58

    # 2. Ingest ghost booking (room 602 has 0 students despite scheduled slot)
    RoomTelemetryAgent.record_sensor_telemetry(
        room_code="602",
        detected_headcount=0,
        sensor_type="EDGE_VISION_CAMERA"
    )

    # 3. Ingest overcrowding (room 603 has 120 students)
    RoomTelemetryAgent.record_sensor_telemetry(
        room_code="603",
        detected_headcount=120,
        sensor_type="EDGE_VISION_CAMERA"
    )

    audit = await RoomTelemetryAgent.audit_room_utilization(
        db=async_db_session,
        day="MON",
        period=3,
        version_id=5
    )
    assert "total_rooms_monitored" in audit
    assert audit["total_rooms_monitored"] > 0
    assert "ghost_bookings" in audit
    assert "overcrowded_rooms" in audit


@pytest.mark.asyncio
async def test_reclaim_ghost_room(async_db_session):
    result = await RoomTelemetryAgent.reclaim_ghost_room(
        db=async_db_session,
        session_id=1,
        room_code="602",
        day="MON",
        period=3,
        purpose="Ad-hoc tutorial"
    )
    assert result["status"] == "RECLAIMED"
    assert result["room_code"] == "602"

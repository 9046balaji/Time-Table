import pytest
from app.core.database import ensure_database, AsyncSessionLocal
from app.services.tool_registry import ToolRegistry


@pytest.mark.asyncio
async def test_phase3_tool_registry_availability_quality_cost():
    await ensure_database()
    async with AsyncSessionLocal() as db:
        # Test availability queries
        avail_rooms = await ToolRegistry.get_room_availability(db, day="MON", period=1)
        assert isinstance(avail_rooms, list)

        avail_fac = await ToolRegistry.get_faculty_availability(db, day="MON", period=1)
        assert isinstance(avail_fac, list)

        alt_room = await ToolRegistry.find_alternative_room(db, day="MON", period=1, min_capacity=40)
        assert alt_room is None or "code" in alt_room

        alt_fac = await ToolRegistry.find_alternative_faculty(db, subject_code="DS", day="MON", period=1)
        assert alt_fac is None or "name" in alt_fac

        # Test weighted change cost model
        orig = [
            {"id": "1", "section": "SEC-A", "day": "MON", "period": 1, "room": "601", "faculty": ["Dr. Reddy"]},
            {"id": "2", "section": "SEC-B", "day": "MON", "period": 2, "room": "602", "faculty": ["P. Girija"]}
        ]
        cand = [
            {"id": "1", "section": "SEC-A", "day": "MON", "period": 1, "room": "604", "faculty": ["Dr. Reddy"]},  # Room changed (+1)
            {"id": "2", "section": "SEC-B", "day": "MON", "period": 2, "room": "602", "faculty": ["K. Nikhitha"]} # Faculty changed (+5)
        ]

        metrics = await ToolRegistry.calculate_disruption_metrics(orig, cand)
        assert metrics["moved_entries"] == 2
        assert metrics["weighted_change_cost"] == 6.0  # 1 + 5 = 6.0

        # Test composite schedule quality evaluator
        quality = await ToolRegistry.calculate_schedule_quality(cand)
        assert "quality_score" in quality
        assert quality["is_valid"] is True

        # Test timetable compare tool
        diff = await ToolRegistry.compare_timetables(orig, cand)
        assert diff["moved_count"] == 2
        assert len(diff["diffs"]) == 2

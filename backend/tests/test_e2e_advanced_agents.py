import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_e2e_advanced_agents_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Substitute candidates API
        sub_res = await client.post(
            "/api/v1/agent/substitute/find-candidates",
            json={"faculty_name": "Dr. S. Srikantha Reddy", "day": "MON", "period": 1, "version_id": 5}
        )
        assert sub_res.status_code == 200
        sub_data = sub_res.json()
        assert "candidates" in sub_data
        assert len(sub_data["candidates"]) > 0

        # 2. Exam scheduler API
        exam_res = await client.post(
            "/api/v1/agent/exam/generate",
            json={"exam_type": "MID_TERM_1", "start_date": "2026-10-12", "num_days": 3, "target_sections": ["II AIML-A", "II AIML-B"]}
        )
        assert exam_res.status_code == 200
        exam_data = exam_res.json()
        assert exam_data["status"] == "COMPLETED"
        assert exam_data["total_exams_scheduled"] > 0

        # 3. Pareto evaluation API
        pareto_res = await client.post(
            "/api/v1/agent/pareto/evaluate",
            json={"version_id": 5}
        )
        assert pareto_res.status_code == 200
        pareto_data = pareto_res.json()
        assert "profile_scores" in pareto_data
        assert "FACULTY_CENTRIC" in pareto_data["profile_scores"]

        # 4. Telemetry record & audit API
        tel_res = await client.post(
            "/api/v1/agent/telemetry/occupancy",
            json={"room_code": "604", "detected_headcount": 0, "sensor_type": "EDGE_VISION_CAMERA"}
        )
        assert tel_res.status_code == 200

        audit_res = await client.get("/api/v1/agent/telemetry/audit?day=MON&period=3&version_id=5")
        assert audit_res.status_code == 200
        audit_data = audit_res.json()
        assert "total_rooms_monitored" in audit_data

        # 5. Reclaim ghost room API
        reclaim_res = await client.post(
            "/api/v1/agent/telemetry/reclaim",
            json={"session_id": 1, "room_code": "604", "day": "MON", "period": 3, "purpose": "Remedial lab"}
        )
        assert reclaim_res.status_code == 200
        assert reclaim_res.json()["status"] == "RECLAIMED"

        # 6. Hierarchical decomposition API
        hier_res = await client.post(
            "/api/v1/agent/hierarchical/solve",
            json={"version_id": 5, "timeout_seconds": 10}
        )
        assert hier_res.status_code == 200
        hier_data = hier_res.json()
        assert hier_data["status"] == "COMPLETED"

        # 7. iCalendar Exports
        sec_ical = await client.get("/api/v1/export/ical/section/II_AIML_A")
        assert sec_ical.status_code == 200
        assert "BEGIN:VCALENDAR" in sec_ical.text

        cohort_ical = await client.get("/api/v1/export/ical/cohort/YEAR_2")
        assert cohort_ical.status_code == 200
        assert "BEGIN:VCALENDAR" in cohort_ical.text

        master_ical = await client.get("/api/v1/export/ical/master")
        assert master_ical.status_code == 200
        assert "BEGIN:VCALENDAR" in master_ical.text

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_unified_3_stage_creation_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # STAGE 1: Fast AI Wizard Generation
        wizard_payload = {
            "branch": "AIML",
            "year_level": "II Year",
            "sections": ["II AIML-A"],
            "preferred_block": "Block-VI (601-619)",
            "max_daily_teaching_hours": 4,
            "max_classes_per_teacher_per_day": 4,
            "assignments": [
                {
                    "subject_code": "DS",
                    "subject_name": "Data Structures",
                    "subject_type": "L",
                    "weekly_hours": 4,
                    "faculty_name": "Dr. Faculty A"
                },
                {
                    "subject_code": "DS(P)",
                    "subject_name": "Data Structures Lab",
                    "subject_type": "P",
                    "weekly_hours": 2,
                    "continuous_slots": 2,
                    "faculty_name": "Dr. Faculty A"
                },
                {
                    "subject_code": "SFCDS",
                    "subject_name": "Statistical Foundations",
                    "subject_type": "L",
                    "weekly_hours": 4,
                    "faculty_name": "Dr. Faculty B"
                }
            ]
        }
        res_wiz = await client.post("/api/v1/solve/generate-from-wizard", json=wizard_payload)
        assert res_wiz.status_code == 200
        wiz_data = res_wiz.json()
        assert wiz_data["status"] in ("OPTIMAL", "FEASIBLE")
        created_version_id = wiz_data.get("version_id")
        assert created_version_id is not None

        # STAGE 2: 7-Agent Society Audit on Newly Generated Version
        res_audit = await client.get(f"/api/v1/agent/multi-agent/audit?version_id={created_version_id}")
        assert res_audit.status_code == 200
        audit_data = res_audit.json()
        assert "votes" in audit_data
        assert len(audit_data["votes"]) == 7
        agent_names = {v["agent"] for v in audit_data["votes"]}
        assert "SectionCurriculumAgent" in agent_names
        assert "FacultyWorkloadAgent" in agent_names
        assert "VenueBlockAgent" in agent_names
        assert "TemporalFlowAgent" in agent_names
        assert "StudentWelfareAgent" in agent_names
        assert "LabTechInfraAgent" in agent_names
        assert "ValidatorAgent" in agent_names

        # STAGE 3: Multi-Agent Synthesis & Publish Gate
        publish_payload = {
            "version_label": f"LIFECYCLE-V{created_version_id}",
            "entries": wiz_data.get("entries", []),
            "session_id": 1
        }
        res_pub = await client.post("/api/v1/agent/multi-agent/publish", json=publish_payload)
        assert res_pub.status_code == 200
        pub_data = res_pub.json()
        assert "version_id" in pub_data

        # STAGE 4: Schedule Workbench Query Verification
        res_vers = await client.get("/api/v1/timetable/versions")
        assert res_vers.status_code == 200
        v_list = res_vers.json()
        assert len(v_list) > 0
        latest_ids = {v["id"] for v in v_list}
        assert created_version_id in latest_ids

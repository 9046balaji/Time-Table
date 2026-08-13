import pytest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

client = TestClient(app)


def test_wizard_solve_endpoint():
    payload = {
        "branch": "AIML",
        "year_level": "II Year",
        "sections": ["II AIML-A", "II AIML-B"],
        "preferred_block": "Block-VI (601-619)",
        "max_daily_teaching_hours": 5,
        "max_classes_per_teacher_per_day": 5,
        "assignments": [
            {
                "subject_code": "DS",
                "subject_name": "Data Structures",
                "subject_type": "L",
                "faculty_name": "Dr. S. Srikantha Reddy",
                "weekly_hours": 3,
                "continuous_slots": 1
            },
            {
                "subject_code": "AI(P)",
                "subject_name": "Artificial Intelligence Lab",
                "subject_type": "P",
                "faculty_name": "Dr. B. Sudha Rani",
                "weekly_hours": 2,
                "continuous_slots": 2
            }
        ]
    }

    response = client.post("/api/v1/solve/generate-from-wizard", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["hard_violations"] == 0
    assert data["entries_count"] > 0



def test_wizard_solve_multi_faculty_lab():
    payload = {
        "branch": "AIML",
        "year_level": "II Year",
        "sections": ["II AIML-A", "II AIML-B"],
        "preferred_block": "Block-VI (601-619)",
        "max_classes_per_teacher_per_day": 5,
        "assignments": [
            {
                "subject_code": "DS(P)",
                "subject_name": "Data Structures Lab",
                "subject_type": "P",
                "faculty_name": "Dr. S. Srikantha Reddy",
                "co_faculty": ["P. Girija", "K. Nikhitha", "Mr. Mahendra Varma"],
                "weekly_hours": 2,
                "continuous_slots": 2
            },
            {
                "subject_code": "DBMS",
                "subject_name": "Database Management Systems",
                "subject_type": "L",
                "faculty_name": "P. Girija",
                "weekly_hours": 3,
                "continuous_slots": 1
            }
        ]
    }

    response = client.post("/api/v1/solve/generate-from-wizard", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["hard_violations"] == 0
    assert data["entries_count"] > 0



def test_wizard_solve_iii_year_with_minor_honors():
    payload = {
        "branch": "AIML",
        "year_level": "III Year",
        "sections": ["III AIML-A", "III AIML-B"],
        "preferred_block": "AFTF High-GPU Labs",
        "max_daily_teaching_hours": 5,
        "max_classes_per_teacher_per_day": 5,
        "assignments": [
            {
                "subject_code": "DL(P)",
                "subject_name": "Deep Learning Practical Lab",
                "subject_type": "P",
                "faculty_name": "Dr. Eva Patel",
                "co_faculty": ["V. Amarnath"],
                "weekly_hours": 2,
                "continuous_slots": 2
            },
            {
                "subject_code": "MINORHONOR",
                "subject_name": "Synchronized Minors / Honors",
                "subject_type": "P",
                "faculty_name": "A. Hruday Raj",
                "weekly_hours": 2,
                "continuous_slots": 2
            }
        ]
    }

    response = client.post("/api/v1/solve/generate-from-wizard", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["hard_violations"] == 0
    assert data["entries_count"] in (8, 16)



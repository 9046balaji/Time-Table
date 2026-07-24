import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_export_excel_endpoint():
    response = client.post("/api/v1/export/excel")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(response.content) > 1000  # Non-empty binary Excel workbook file


def test_export_pdf_endpoint():
    response = client.post("/api/v1/export/pdf/sections")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000


def test_sync_smartclass_endpoint():
    response = client.post("/api/v1/timetable/sync-master")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["sections_synced"] == 44
    assert data["master_slots_synced"] == 1000


if __name__ == "__main__":
    test_export_excel_endpoint()
    test_export_pdf_endpoint()
    test_sync_smartclass_endpoint()

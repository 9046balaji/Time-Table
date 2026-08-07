import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.mark.asyncio
async def test_ical_export_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res = await ac.get("/api/v1/export/ical/faculty/1")
        assert res.status_code == 200
        assert "text/calendar" in res.headers["content-type"]
        text = res.text
        assert "BEGIN:VCALENDAR" in text
        assert "END:VCALENDAR" in text


@pytest.mark.asyncio
async def test_telemetry_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res = await ac.get("/api/v1/telemetry/metrics")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "UP"
        assert "system" in data
        assert "services" in data

import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.mark.asyncio
async def test_solver_benchmark_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res = await ac.post("/api/v1/solve/benchmark")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "COMPLETED"
        assert data["total_sections"] == 44
        assert data["total_faculty"] == 72
        assert "benchmark_runtime_seconds" in data

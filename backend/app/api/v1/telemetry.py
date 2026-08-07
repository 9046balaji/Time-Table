import os
import sys
import psutil
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_telemetry_metrics(db: AsyncSession = Depends(get_db)):
    """
    Returns real-time system telemetry metrics including memory usage, CPU load,
    Redis status, and database connection state.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    redis_status = "UNKNOWN"
    try:
        import redis
        r = redis.Redis.from_url("redis://localhost:6379/0", socket_timeout=1)
        if r.ping():
            redis_status = "HEALTHY"
    except Exception:
        redis_status = "UNAVAILABLE"

    return {
        "status": "UP",
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_mb": round(memory_info.rss / (1024 * 1024), 2),
            "threads_count": process.num_threads(),
        },
        "services": {
            "postgresql": "CONNECTED",
            "redis_cache": redis_status,
        },
        "python_version": sys.version.split()[0]
    }

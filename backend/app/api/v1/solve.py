import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.solver.csat_solver import SolverConfig
from app.services.solve_service import SolveService
from app.core.database import get_db

router = APIRouter()


@router.post("", response_model=Dict[str, Any])
async def trigger_solver(config: SolverConfig = SolverConfig(), db: AsyncSession = Depends(get_db)):
    return await SolveService.start_solve_job(db=db, config=config)


@router.post("/benchmark", response_model=Dict[str, Any])
async def benchmark_solver():
    """Run full-scale CP-SAT benchmark test generating timetables for 44 sections and 72 faculty."""
    return await SolveService.run_benchmark_suite()


@router.get("/{run_id}/status", response_model=Dict[str, Any])
async def get_solver_status(run_id: str):
    status = SolveService.get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Solver run not found.")
    return status


@router.post("/{run_id}/abort", response_model=Dict[str, Any])
async def abort_solver_run(run_id: str):
    aborted = SolveService.abort_run(run_id)
    if not aborted:
        raise HTTPException(status_code=404, detail="Active solver run not found or already finished.")
    return {"status": "ABORTED", "run_id": run_id, "message": f"Solver run {run_id} has been aborted."}



@router.websocket("/{run_id}/stream")
async def websocket_solver_stream(websocket: WebSocket, run_id: str):
    await websocket.accept()
    
    # Try connecting to Redis Pub/Sub channel
    try:
        import aioredis
        r_client = aioredis.from_url("redis://redis:6379/0", decode_responses=True)
        pubsub = r_client.pubsub()
        await pubsub.subscribe(f"solver_progress:{run_id}")

        async for message in pubsub.listen():
            if message and message.get("type") == "message":
                data = message.get("data")
                if data:
                    await websocket.send_text(data)
                    # Close socket if task completed or failed
                    data_json = json.loads(data)
                    if data_json.get("type") in ("complete", "error"):
                        break
        await pubsub.unsubscribe(f"solver_progress:{run_id}")
        await r_client.close()
    except Exception as ex:
        # Real memory status polling fallback when Redis Pub/Sub is unavailable
        prev_gen = -1
        for _ in range(120):  # Poll up to 60 seconds
            status = SolveService.get_run_status(run_id)
            if status:
                gen = status.get("generation", 0)
                st = status.get("status", "RUNNING")
                if gen != prev_gen or st in ("COMPLETED", "FAILED", "ABORTED"):
                    prev_gen = gen
                    msg = {
                        "type": "complete" if st == "COMPLETED" else ("error" if st in ("FAILED", "ABORTED") else "progress"),
                        "status": st,
                        "generation": gen,
                        "fitness": status.get("fitness_score", 0),
                        "hard_violations": status.get("hard_violations", 0),
                        "soft_violations": status.get("soft_violations", 0),
                        "runtime_seconds": status.get("runtime_seconds", 0.0),
                        "message": f"Status: {st} (Gen {gen}, Hard Violations: {status.get('hard_violations', 0)})"
                    }
                    await websocket.send_text(json.dumps(msg))
                    if st in ("COMPLETED", "FAILED", "ABORTED"):
                        break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

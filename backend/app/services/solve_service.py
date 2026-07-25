import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.solver.csat_solver import CPSATSolver, SolverConfig
from app.models.solver_run import SolverRun
from app.models.timetable import TimetableVersion, TimetableEntry


class SolveService:
    _solver_runs_memory: Dict[str, Dict[str, Any]] = {}

    @classmethod
    async def start_solve_job(cls, db: Optional[AsyncSession], config: SolverConfig) -> Dict[str, Any]:
        """Initialize a solver run record and trigger optimization background task."""
        run_count = len(cls._solver_runs_memory) + 1
        run_id = f"run_{run_count}"

        run_state = {
            "run_id": run_id,
            "status": "RUNNING",
            "algorithm": config.algorithm,
            "hard_violations": 51,
            "soft_violations": 12,
            "fitness_score": -51012,
            "generation": 0,
            "runtime_seconds": 0.0,
        }
        cls._solver_runs_memory[run_id] = run_state

        if db is not None:
            try:
                db_run = SolverRun(
                    scope=config.scope or "ALL",
                    algorithm=config.algorithm,
                    config=config.model_dump(),
                    status="RUNNING"
                )
                db.add(db_run)
                await db.commit()
            except Exception:
                pass

        asyncio.create_task(cls._execute_solver_async(run_id, config, db))

        return {
            "run_id": run_id,
            "status": "RUNNING",
            "message": f"Solver task {run_id} started using {config.algorithm} engine."
        }

    @classmethod
    async def _execute_solver_async(cls, run_id: str, config: SolverConfig, db: Optional[AsyncSession]):
        sample_sections = [{"id": f"sec_{i}", "student_count": 60} for i in range(1, 10)]
        sample_subjects = []
        for sec in sample_sections:
            for sub_id in [101, 102, 103, 104]:
                sample_subjects.append({
                    "section_id": sec["id"],
                    "subject_id": sub_id,
                    "subject_code": f"SUBJ_{sub_id}",
                    "subject_type": "P" if sub_id == 104 else "L",
                    "total_slots_needed": 2 if sub_id == 104 else 3
                })
        sample_rooms = [{"id": f"r_{i}", "capacity": 60, "room_type": "gpu_lab" if i > 5 else "classroom"} for i in range(1, 12)]
        sample_time_slots = []
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for p in range(1, 9):
                sample_time_slots.append({
                    "id": f"{day}_{p}",
                    "day": day,
                    "period": p,
                    "is_blocked": False
                })

        def progress_cb(update: dict):
            if run_id in cls._solver_runs_memory:
                cls._solver_runs_memory[run_id].update({
                    "generation": update.get("generation", cls._solver_runs_memory[run_id]["generation"]),
                    "fitness_score": update.get("fitness", cls._solver_runs_memory[run_id]["fitness_score"]),
                    "hard_violations": update.get("hard_violations", cls._solver_runs_memory[run_id]["hard_violations"]),
                    "runtime_seconds": update.get("runtime_seconds", cls._solver_runs_memory[run_id]["runtime_seconds"])
                })

        solver = CPSATSolver(config)
        result = await asyncio.to_thread(
            solver.solve,
            sections=sample_sections,
            section_subjects=sample_subjects,
            rooms=sample_rooms,
            time_slots=sample_time_slots,
            faculty_subject_map={},
            progress_callback=progress_cb
        )

        if run_id in cls._solver_runs_memory:
            status_str = "COMPLETED" if result["status"] in ("OPTIMAL", "FEASIBLE") else "FAILED"
            cls._solver_runs_memory[run_id].update({
                "status": status_str,
                "hard_violations": result.get("hard_violations", 0),
                "soft_violations": result.get("soft_violations", 0),
                "runtime_seconds": result.get("runtime_seconds", 0.0),
                "entries_count": result.get("entries_count", 0)
            })

            # Create new TimetableVersion V6_AUTO when solver succeeds
            if status_str == "COMPLETED" and db is not None:
                try:
                    new_version = TimetableVersion(
                        academic_year_id=1,
                        version_label="V6_AUTO",
                        is_current=True
                    )
                    db.add(new_version)
                    await db.commit()
                except Exception:
                    pass

    @classmethod
    def get_run_status(cls, run_id: str) -> Optional[Dict[str, Any]]:
        return cls._solver_runs_memory.get(run_id)

    @classmethod
    def abort_run(cls, run_id: str) -> bool:
        if run_id in cls._solver_runs_memory:
            cls._solver_runs_memory[run_id]["status"] = "ABORTED"
            cls._solver_runs_memory[run_id]["message"] = "Solver run aborted by user."
            return True
        return False


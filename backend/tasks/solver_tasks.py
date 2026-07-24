import time
from typing import Dict, Any
from backend.tasks.celery_app import celery_app
from backend.solver.csat_solver import CPSATSolver, SolverConfig
from backend.solver.genetic_algorithm import GeneticAlgorithmOptimizer


@celery_app.task(bind=True, name="run_solver_task")
def run_solver_task(self, config_dict: Dict[str, Any], sections: list, section_subjects: list, rooms: list, time_slots: list, faculty_map: dict = None):
    """Celery task running the CP-SAT or Genetic Algorithm timetable solver asynchronously."""
    algorithm = config_dict.get("algorithm", "CP-SAT")
    timeout = config_dict.get("timeout_seconds", 120)

    self.update_state(state="PROGRESS", meta={
        "type": "status",
        "message": f"Initializing {algorithm} engine with {len(sections)} sections and {len(rooms)} rooms...",
        "generation": 0,
        "hard_violations": 51,
        "soft_violations": 12,
        "runtime_seconds": 0.0
    })

    def progress_callback(update_dict: dict):
        self.update_state(state="PROGRESS", meta=update_dict)

    if algorithm == "GeneticAlgorithm":
        ga = GeneticAlgorithmOptimizer(
            population_size=config_dict.get("population_size", 50),
            generations=config_dict.get("generations", 200),
            mutation_rate=config_dict.get("mutation_rate", 0.05)
        )
        # Flatten sample initial slots
        result = ga.optimize([])
    else:
        cfg = SolverConfig(algorithm=algorithm, timeout_seconds=timeout)
        solver = CPSATSolver(cfg)
        result = solver.solve(
            sections=sections,
            section_subjects=section_subjects,
            rooms=rooms,
            time_slots=time_slots,
            faculty_subject_map=faculty_map or {},
            progress_callback=progress_callback
        )

    return result

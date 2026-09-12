import random
import time
from typing import List, Dict, Any, Tuple, Optional
from backend.solver.fitness import FitnessEvaluator


class GeneticAlgorithmOptimizer:
    """
    Heuristic Genetic Algorithm Optimizer for timetable fine-tuning and soft constraint minimization.
    """

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.05,
        elite_size: int = 5
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_size = min(elite_size, population_size // 2)

    def optimize(self, initial_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes population generation, tournament selection, crossover, and mutation.
        Returns optimized entries dictionary with runtime and fitness metrics.
        """
        start_time = time.time()
        if not initial_entries:
            return {
                "algorithm": "GeneticAlgorithm",
                "runtime_seconds": 0.0,
                "generations": 0,
                "fitness_score": 0,
                "hard_violations": 0,
                "soft_violations": 0,
                "optimized_entries": []
            }

        # Initialize Population from seed variant perturbations
        population: List[List[Dict[str, Any]]] = [initial_entries]
        for _ in range(1, self.population_size):
            variant = [dict(e) for e in initial_entries]
            # Perturb ~5% of entries into valid period ranges (1..8)
            for item in variant:
                if random.random() < 0.05:
                    item["period"] = random.randint(1, 8)
            population.append(variant)

        best_individual = initial_entries
        best_eval = FitnessEvaluator.evaluate(best_individual)

        # Collect valid room codes from initial candidate set
        candidate_rooms = list({str(e.get("room", "")).strip() for e in initial_entries if e.get("room")})

        for gen in range(1, self.generations + 1):
            # Evaluate Population
            evaluations = [(ind, FitnessEvaluator.evaluate(ind)) for ind in population]
            evaluations.sort(key=lambda x: x[1]["fitness_score"], reverse=True)

            current_best, current_best_eval = evaluations[0]
            if current_best_eval["fitness_score"] > best_eval["fitness_score"]:
                best_individual = current_best
                best_eval = current_best_eval

            # Elitism: retain top performers
            new_population = [evaluations[i][0] for i in range(self.elite_size)]

            # Generate remaining population through crossover & mutation
            while len(new_population) < self.population_size:
                p1 = self._tournament_select(evaluations)
                p2 = self._tournament_select(evaluations)
                child = self._crossover(p1, p2)
                child = self._mutate(child, candidate_rooms=candidate_rooms)
                new_population.append(child)

            population = new_population

        runtime = round(time.time() - start_time, 2)

        # Enforce zero-hard-violation ConflictChecker validation gate (Risk D)
        from backend.solver.conflict_checker import ConflictChecker
        checker = ConflictChecker()
        report = checker.detect(best_individual)

        is_validated = report.total_hard_violations == 0
        return {
            "algorithm": "GeneticAlgorithm",
            "runtime_seconds": runtime,
            "generations": self.generations,
            "fitness_score": best_eval["fitness_score"],
            "hard_violations": report.total_hard_violations,
            "soft_violations": best_eval["soft_violations"],
            "is_validated": is_validated,
            "validation_passed": is_validated,
            "optimized_entries": best_individual
        }

    def _tournament_select(
        self, evaluations: List[Tuple[List[Dict[str, Any]], Dict[str, Any]]], k: int = 3
    ) -> List[Dict[str, Any]]:
        competitors = random.sample(evaluations, min(k, len(evaluations)))
        competitors.sort(key=lambda x: x[1]["fitness_score"], reverse=True)
        return competitors[0][0]

    def _crossover(
        self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if len(parent1) <= 1:
            return [dict(e) for e in parent1]
        cut = random.randint(1, len(parent1) - 1)
        child = [dict(e) for e in parent1[:cut]] + [dict(e) for e in parent2[cut:]]
        return child

    def _mutate(
        self, individual: List[Dict[str, Any]], candidate_rooms: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Multi-dimensional genetic mutation perturbing period, day, or room allocation."""
        mutated = [dict(e) for e in individual]
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        rooms = candidate_rooms or list({str(e.get("room", "")).strip() for e in individual if e.get("room")})

        for item in mutated:
            if random.random() < self.mutation_rate:
                roll = random.random()
                if roll < 0.60:
                    # Period shift (1..8)
                    item["period"] = random.randint(1, 8)
                elif roll < 0.85:
                    # Day redistribution (labs avoid Saturday)
                    stype = str(item.get("type") or item.get("entry_type") or "L").upper()
                    allowed_days = days[:5] if stype in ("P", "LAB") else days
                    item["day"] = random.choice(allowed_days)
                elif rooms:
                    # Alternative venue mutation
                    item["room"] = random.choice(rooms)
        return mutated



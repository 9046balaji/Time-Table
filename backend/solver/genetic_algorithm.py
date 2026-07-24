import random
import time
from typing import List, Dict, Any, Tuple
from backend.solver.fitness import FitnessEvaluator


class GeneticAlgorithmOptimizer:
    def __init__(self, population_size: int = 50, generations: int = 100, mutation_rate: float = 0.05, elite_size: int = 5):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_size = min(elite_size, population_size // 2)

    def optimize(self, initial_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            # Randomly perturb 5% of period slots
            for item in variant:
                if random.random() < 0.05:
                    item["period"] = random.randint(1, 8)
            population.append(variant)

        best_individual = initial_entries
        best_eval = FitnessEvaluator.evaluate(best_individual)

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
                child = self._mutate(child)
                new_population.append(child)

            population = new_population

        runtime = round(time.time() - start_time, 2)
        return {
            "algorithm": "GeneticAlgorithm",
            "runtime_seconds": runtime,
            "generations": self.generations,
            "fitness_score": best_eval["fitness_score"],
            "hard_violations": best_eval["hard_violations"],
            "soft_violations": best_eval["soft_violations"],
            "optimized_entries": best_individual
        }

    def _tournament_select(self, evaluations: List[Tuple[List[Dict[str, Any]], Dict[str, Any]]], k: int = 3) -> List[Dict[str, Any]]:
        competitors = random.sample(evaluations, min(k, len(evaluations)))
        competitors.sort(key=lambda x: x[1]["fitness_score"], reverse=True)
        return competitors[0][0]

    def _crossover(self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(parent1) <= 1:
            return [dict(e) for e in parent1]
        cut = random.randint(1, len(parent1) - 1)
        child = [dict(e) for e in parent1[:cut]] + [dict(e) for e in parent2[cut:]]
        return child

    def _mutate(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        mutated = [dict(e) for e in individual]
        for item in mutated:
            if random.random() < self.mutation_rate:
                item["period"] = random.randint(1, 8)
        return mutated


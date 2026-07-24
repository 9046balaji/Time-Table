import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.solver.fitness import FitnessEvaluator
from backend.solver.genetic_algorithm import GeneticAlgorithmOptimizer


def test_fitness_evaluator():
    sample_entries = [
        {"day": "MON", "period": 1, "faculty_list": ["Dr. P. Kalpana"]},
        {"day": "MON", "period": 2, "faculty_list": ["Dr. P. Kalpana"]},
        {"day": "MON", "period": 4, "faculty_list": ["Dr. P. Kalpana"]},
        {"day": "MON", "period": 5, "faculty_list": ["Dr. P. Kalpana"]},
        {"day": "MON", "period": 7, "faculty_list": ["Dr. P. Kalpana"]},  # 5th hour in day > 4 max cap
    ]

    res = FitnessEvaluator.evaluate(sample_entries)
    assert res["soft_penalty_points"] > 0, "Should penalize faculty teaching > 4 hours in a single day"


def test_genetic_algorithm_optimizer():
    ga = GeneticAlgorithmOptimizer(population_size=10, generations=20)
    initial = [
        {"section": "II AIML-A", "day": "MON", "period": 1, "faculty_list": ["Dr. P. Kalpana"]},
        {"section": "II AIML-A", "day": "MON", "period": 2, "faculty_list": ["Dr. P. Kalpana"]},
    ]
    opt_result = ga.optimize(initial)

    assert opt_result["generations"] == 20
    assert "fitness_score" in opt_result


if __name__ == "__main__":
    test_fitness_evaluator()
    test_genetic_algorithm_optimizer()

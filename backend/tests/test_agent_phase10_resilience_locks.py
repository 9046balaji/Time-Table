import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.solver.genetic_algorithm import GeneticAlgorithmOptimizer


def test_phase10_ga_validation_gate():
    # Test GA Optimizer zero-hard-violation ConflictChecker validation gate (Risk D)
    ga = GeneticAlgorithmOptimizer(population_size=10, generations=5)
    initial_entries = [
        {"section": "SEC-A", "subject": "DS", "room": "601", "day": "MON", "period": 1, "faculty": ["Dr. Reddy"]}
    ]
    res = ga.optimize(initial_entries)

    assert res["algorithm"] == "GeneticAlgorithm"
    assert "is_validated" in res
    assert "validation_passed" in res
    assert res["is_validated"] is True

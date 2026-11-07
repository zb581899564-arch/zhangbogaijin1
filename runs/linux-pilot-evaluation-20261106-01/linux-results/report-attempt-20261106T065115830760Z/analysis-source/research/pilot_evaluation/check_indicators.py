"""Focused mathematical fixtures, invoked only by the Linux check runner."""
import math

import numpy as np

from .check_helpers import assert_raises, inclusion_exclusion_hv
from .indicators import (ObjectiveScale, ReferenceSet, evaluate_front, exact_coverage,
                         hypervolume, igd, igd_plus, objective_extremes,
                         reference_points, shared_final_reference)
from .summaries import igd_plus_symmetric_effect, paired_summary


def check_hv_and_distances():
    front = [[0.2, 0.7, 0.5], [0.5, 0.2, 0.4], [0.3, 0.4, 0.8],
             [0.9, 0.9, 0.9], [0.2, 0.7, 0.5], [1.2, 0.1, 0.1]]
    expected = inclusion_exclusion_hv(front, [1, 1, 1])
    assert math.isclose(hypervolume(front, [1, 1, 1]), expected, abs_tol=1e-12)
    assert igd([[0, 0, 0]], [[1, 0, 0], [3, 0, 0]]) == 2.0
    assert igd([[1, 0, 0], [3, 0, 0]], [[0, 0, 0]]) == 1.0
    assert igd_plus([[0, 0, 0]], [[1, 0, 0]]) == 0.0
    assert igd_plus([[2, 0, 0]], [[1, 0, 0]]) == 1.0
    assert igd([[0, 0, 0]], [[1, 0, 0]]) == 1.0
    assert math.isinf(igd([], [[1, 1, 1]]))
    assert math.isinf(igd_plus([], [[1, 1, 1]]))
    assert_raises(ValueError, igd, [[1, 1, 1]], [])
    assert_raises(ValueError, igd_plus, [[1, 1, 1]], [])
    assert_raises(ValueError, hypervolume, [[1, 2]], [3, 3, 3])
    assert_raises(ValueError, igd, [[float("nan"), 1, 1]], [[1, 1, 1]])
    assert_raises(ValueError, igd, [1, 2, 3], [[1, 1, 1]])


def check_coverage_and_reference():
    equal = exact_coverage([[1, 2, 3], [1, 2, 3]], [[1, 2, 3]])
    assert equal["C_A_B"] == equal["C_B_A"] == 1.0
    assert equal["totalA"] == equal["totalB"] == equal["sharedObjectiveVectors"] == 1
    disjoint = exact_coverage([[1, 3, 1]], [[3, 1, 1]])
    assert disjoint["C_A_B"] == disjoint["C_B_A"] == 0.0
    assert_raises(ValueError, exact_coverage, [], [[1, 1, 1]])
    reference = shared_final_reference({"A/1": [[1, 3, 2], [4, 4, 4]],
                                        "B/1": [[3, 1, 2], [1, 3, 2]]})
    np.testing.assert_array_equal(reference_points(reference), [[1, 3, 2], [3, 1, 2]])
    assert reference.source_ids == ("A/1", "B/1")
    assert_raises(ValueError, reference_points, reference, online=True, current_step=1000)
    assert_raises(ValueError, shared_final_reference, {"A": [[1, 1, 1]]}, online=True)
    assert_raises(ValueError, shared_final_reference, {"A": []})
    assert_raises(ValueError, reference_points, [[1, 1, 1]], online=True, current_step=100)
    frozen = ReferenceSet(((1, 1, 1),), ("frozen-independent",), False, 10)
    assert_raises(ValueError, reference_points, frozen, online=True, current_step=9)
    np.testing.assert_array_equal(reference_points(frozen, online=True, current_step=10), [[1, 1, 1]])


def check_normalization_and_extremes():
    scale = ObjectiveScale((0, 0, 0), (10, 10, 10))
    front = [[1, 3, 2], [1, 2, 3], [3, 1, 1]]
    extrema = objective_extremes(front, scale)
    assert extrema["Cmax"]["tie_count"] == 2
    np.testing.assert_array_equal(extrema["Cmax"]["normalized_vectors"], [[0.1, 0.2, 0.3], [0.1, 0.3, 0.2]])
    assert extrema["TEC"]["raw_vectors"] == [[3.0, 1.0, 1.0]]
    reference = shared_final_reference({"one": front})
    result = evaluate_front(front, reference, scale, [1, 1, 1])
    assert result["IGD"] == result["IGDplus"] == 0.0
    expected = inclusion_exclusion_hv(scale.normalize(front), [1, 1, 1])
    assert math.isclose(result["HV"], expected, abs_tol=1e-12)
    assert_raises(ValueError, ObjectiveScale, [0, 0, 0], [1, 0, 1])
    assert_raises(ValueError, evaluate_front, front, reference, scale, [1, 1, 1], online=True)


def check_paired_effects():
    assert igd_plus_symmetric_effect(0, 0) == 0.0
    assert igd_plus_symmetric_effect(0, 2) == 2.0
    assert igd_plus_symmetric_effect(2, 0) == -2.0
    assert math.isclose(igd_plus_symmetric_effect(1, 3), 1.0)
    assert_raises(ValueError, igd_plus_symmetric_effect, -1, 1)
    rows = [{"instance": "a", "seed": seed, "candidate": value, "control": 1}
            for seed, value in enumerate([0, 0, 10])]
    rows.append({"instance": "b", "seed": 0, "candidate": 2, "control": 1})
    result = paired_summary(rows, metric="IGDplus", higher_is_better=False)
    assert result["by_instance"]["a"]["seed_directions"] == {"wins": 2, "ties": 0, "losses": 1}
    assert result["by_instance"]["a"]["paired_improvement"] == {"median": 1.0, "range": [-9.0, 1.0]}
    assert result["instance_median_improvement"]["median"] == 0.0
    assert result["instance_directions"] == {"wins": 1, "ties": 0, "losses": 1}
    assert result["by_instance"]["a"]["symmetric_effect"]["median"] == 2.0
    assert len(result["by_instance"]["a"]["raw"]) == 3
    assert_raises(ValueError, paired_summary, rows + [rows[0]], metric="IGDplus", higher_is_better=False)
    assert_raises(ValueError, paired_summary, rows, metric="IGDplus", higher_is_better=True)

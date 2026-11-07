"""Known exact attainment sets and fixed third-objective conditional sections."""
import numpy as np

from .attainment import (attainment_boundary, attainment_grid, attainment_probability,
                         conditional_eaf_slices, eaf_report, fixed_quartile_thresholds)
from .check_helpers import assert_raises


def check_exact_attainment():
    fronts = {"a1": [[1, 3], [3, 1]], "a2": [[1, 3], [3, 1]],
              "b1": [[2, 2]], "b2": [[2, 2]], "c": [[1, 2], [2, 1]]}
    queries = [[0, 0], [1, 3], [2, 2], [3, 1], [1, 2], [3, 3]]
    np.testing.assert_allclose(attainment_probability(fronts, queries), [0, 0.6, 0.6, 0.6, 0.2, 1])
    boundary = attainment_boundary(fronts)
    assert boundary["corners"] == [[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]]
    assert boundary["step_vertices"] == [[1.0, 3.0], [2.0, 3.0], [2.0, 2.0], [3.0, 2.0], [3.0, 1.0]]
    grid = attainment_grid(fronts)
    assert grid["exact_step_cells"] is True
    np.testing.assert_allclose(grid["probability"], [[0, 0.2, 0.6], [0.2, 0.6, 1], [0.6, 1, 1]])
    report = eaf_report(fronts, include_grid=True)
    assert report["eligible_for_plot"] and report["boundary"] == boundary
    assert_raises(ValueError, attainment_grid, fronts, max_cells=4)
    assert_raises(ValueError, attainment_boundary, fronts, level=0)
    assert_raises(ValueError, attainment_probability, {"bad": [[1, 2, 3]]}, [[1, 1]])


def check_empty_and_three_seed_attainment():
    fronts = {"one": [[1, 1]], "two": [[1, 1]], "three": []}
    np.testing.assert_allclose(attainment_probability(fronts, [[1, 1]]), [2 / 3])
    report = eaf_report(fronts, include_grid=True)
    assert report["status"] == "SUPPRESSED_FEWER_THAN_5_SEEDS"
    assert report["boundary"] is None and report["grid"] is None
    empty = {str(seed): [] for seed in range(5)}
    assert attainment_boundary(empty)["corners"] == []
    assert attainment_grid(empty)["probability"] == []
    np.testing.assert_array_equal(attainment_probability(empty, [[1, 1]]), [0])
    assert_raises(ValueError, attainment_probability, {}, [[1, 1]])


def check_conditional_quartile_sections():
    reference = [[0, 1, 0], [1, 0, 1], [2, 3, 2], [3, 2, 3]]
    thresholds = fixed_quartile_thresholds(reference, condition_axis=2)
    assert thresholds == {"q25": 0.75, "q50": 1.5, "q75": 2.25}
    fronts = {str(seed): [[1, 1, 0.5], [0, 0, 2]] for seed in range(5)}
    result = conditional_eaf_slices(fronts, condition_axis=2, thresholds=thresholds)
    assert result["display_axes"] == [0, 1]
    assert result["slices"]["q25"]["boundary"]["corners"] == [[1.0, 1.0]]
    assert result["slices"]["q50"]["boundary"]["corners"] == [[1.0, 1.0]]
    assert result["slices"]["q75"]["boundary"]["corners"] == [[0.0, 0.0]]
    fronts["2"] = fronts["3"] = fronts["4"] = [[0, 0, 3]]
    empty_runs = conditional_eaf_slices(fronts, condition_axis=2, thresholds=thresholds)
    assert empty_runs["slices"]["q25"]["run_count"] == 5
    assert empty_runs["slices"]["q25"]["boundary"]["corners"] == []
    assert_raises(ValueError, conditional_eaf_slices, fronts, condition_axis=2, thresholds={"q25": 1})
    assert_raises(ValueError, fixed_quartile_thresholds, reference, condition_axis=3)

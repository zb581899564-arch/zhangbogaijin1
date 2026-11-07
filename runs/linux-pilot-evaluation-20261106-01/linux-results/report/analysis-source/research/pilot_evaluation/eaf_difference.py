"""Paired-seed EAF differences on one explicit normalization and common grid."""
import numpy as np

from .attainment import attainment_grid
from .validation import run_fronts, vector


def _paired_normalized(first, second, lower, upper):
    first, second = run_fronts(first, 2), run_fronts(second, 2)
    if set(first) != set(second):
        raise ValueError("EAF difference requires the same paired seed IDs")
    lower, upper = vector(lower, 2), vector(upper, 2)
    if np.any(upper <= lower):
        raise ValueError("Both arms require one common frozen positive normalization range")
    normalize = lambda fronts: {seed: (fronts[seed] - lower) / (upper - lower) for seed in first}
    return normalize(first), normalize(second), lower, upper


def eaf_difference(first, second, *, lower, upper, x=None, y=None, max_cells=2_000_000):
    """Exact A-minus-B attainment probabilities after one common 2D scaling.

    x/y are in normalized coordinates; defaults include both arms' event knots.
    Positive difference means A attains this 2D point more often. It does not
    establish superiority in three objectives or a significance claim.
    """
    first, second, lower, upper = _paired_normalized(first, second, lower, upper)
    all_points = np.vstack([*first.values(), *second.values()])
    xs = np.unique(all_points[:, 0]) if x is None else x
    ys = np.unique(all_points[:, 1]) if y is None else y
    grid_a = attainment_grid(first, x=xs, y=ys, max_cells=max_cells)
    grid_b = attainment_grid(second, x=xs, y=ys, max_cells=max_cells)
    difference = np.asarray(grid_a["probability"]) - np.asarray(grid_b["probability"])
    return {"pairedRunCount": len(first), "seedIDs": list(first), "lower": lower.tolist(), "upper": upper.tolist(),
            "x": grid_a["x"], "y": grid_a["y"], "probabilityA": grid_a["probability"],
            "probabilityB": grid_b["probability"], "differenceAminusB": difference.tolist(),
            "exactStepCells": x is None and y is None,
            "orientation": "difference[y_index][x_index]",
            "signMeaning": "Positive: A attains this 2D point more often; not a three-objective superiority claim"}


def eaf_difference_report(first, second, *, lower, upper, x=None, y=None, max_cells=2_000_000):
    """Presentation gate: at least five matched seeds, otherwise no display."""
    checked_a, checked_b, _, _ = _paired_normalized(first, second, lower, upper)
    if len(checked_a) < 5:
        return {"pairedRunCount": len(checked_a), "eligibleForDisplay": False, "grid": None,
                "status": "SUPPRESSED_FEWER_THAN_5_PAIRED_SEEDS"}
    return {"pairedRunCount": len(checked_a), "eligibleForDisplay": True,
            "status": "AVAILABLE_DESCRIPTIVE_EAF_DIFFERENCE",
            "grid": eaf_difference(first, second, lower=lower, upper=upper, x=x, y=y, max_cells=max_cells)}


def check_eaf_difference():
    """Known probability differences and pairing guards; invoked on Linux only."""
    from .check_helpers import assert_raises
    a = {str(seed): [[2, 4]] for seed in range(5)}
    b = {str(seed): [[4, 2]] for seed in range(5)}
    result = eaf_difference(a, b, lower=[0, 0], upper=[2, 2])
    assert result["x"] == result["y"] == [1.0, 2.0]
    np.testing.assert_array_equal(result["differenceAminusB"], [[0, -1], [1, 0]])
    reverse = eaf_difference(b, a, lower=[0, 0], upper=[2, 2])
    np.testing.assert_array_equal(reverse["differenceAminusB"], -np.asarray(result["differenceAminusB"]))
    assert eaf_difference_report(a, b, lower=[0, 0], upper=[2, 2])["eligibleForDisplay"]
    three = {key: a[key] for key in ("0", "1", "2")}
    suppressed = eaf_difference_report(three, three, lower=[0, 0], upper=[2, 2])
    assert suppressed["grid"] is None and not suppressed["eligibleForDisplay"]
    assert_raises(ValueError, eaf_difference, a, three, lower=[0, 0], upper=[2, 2])
    assert_raises(ValueError, eaf_difference, a, b, lower=[0, 0], upper=[0, 2])

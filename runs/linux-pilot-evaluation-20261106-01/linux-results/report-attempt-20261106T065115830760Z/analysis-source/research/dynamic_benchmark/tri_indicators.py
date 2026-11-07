"""Joint reporting of HV, IGD+ and both coverage directions; no search decisions."""
import numpy as np

from research.expansion_audit.metrics import coverage


def objective_set(points):
    """Deduplicate objective vectors, without pruning or changing their precision."""
    front = np.asarray(points, dtype=float)
    if front.size == 0:
        return np.empty((0, 3))
    if front.ndim != 2 or front.shape[1] != 3 or not np.isfinite(front).all():
        raise ValueError("Expected finite three-objective vectors")
    return np.unique(front, axis=0)


def bidirectional_coverage(first, second):
    """Exact weak minimization dominance; equal vectors count in both directions.

    Empty fronts are not comparable here: callers must report the missing or
    failed run rather than substitute a coverage value with a zero denominator.
    """
    a, b = objective_set(first), objective_set(second)
    if not len(a) or not len(b):
        raise ValueError("Coverage comparison requires two nonempty fronts")
    ab, ba = coverage(a, b), coverage(b, a)
    return {
        "C_A_B": ab, "C_B_A": ba,
        "coveredB": round(ab * len(b)), "totalB": len(b),
        "coveredA": round(ba * len(a)), "totalA": len(a),
        "sharedObjectiveVectors": len(set(map(tuple, a)) & set(map(tuple, b))),
    }


def directional_description(hv_effect, igd_worsening, c_ab, c_ba):
    """Descriptive signs only, not a gate, significance test or weighted score.

    The C sign compares two reported coverage fractions with different target
    sets. It describes coverage asymmetry, not a total order on Pareto fronts.
    """
    def sign(value):
        return 1 if value > 1e-12 else -1 if value < -1e-12 else 0

    signs = {"HV": sign(hv_effect), "IGDplus": sign(-igd_worsening),
             "coverageAsymmetry": sign(c_ab - c_ba)}
    values = list(signs.values())
    if min(values) >= 0 and max(values) > 0:
        label = "ALIGNED_TOWARD_A"
    elif max(values) <= 0 and min(values) < 0:
        label = "ALIGNED_TOWARD_B"
    elif min(values) == max(values) == 0:
        label = "NO_DIRECTIONAL_DIFFERENCE"
    else:
        label = "MIXED_DIRECTIONS"
    return {"signsFavouringA": signs, "label": label,
            "coverageUninformative": abs(c_ab - c_ba) <= 1e-12}

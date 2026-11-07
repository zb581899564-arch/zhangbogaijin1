"""Exact empirical attainment for minimization; no projection masquerading as 3D."""
from fractions import Fraction
from math import ceil

import numpy as np

from .indicators import reference_points
from .validation import finite, integer, points, run_fronts


def attainment_probability(fronts, queries):
    """Fraction of runs with any point weakly dominating each 2D query.

    Empty valid fronts stay in the denominator. Failed or missing runs must be
    reported separately, never silently omitted or presented as empty successes.
    """
    fronts, queries = run_fronts(fronts, 2), points(queries, 2)
    counts = np.zeros(len(queries), dtype=int)
    for front in fronts.values():
        for start in range(0, len(queries), 256):
            attained = np.all(front[:, None, :] <= queries[None, start:start + 256, :], axis=2)
            counts[start:start + 256] += attained.any(axis=0)
    return counts / len(fronts)


def _axis(values, all_points, axis):
    if values is None:
        return np.unique(all_points[:, axis])
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or not np.isfinite(result).all():
        raise ValueError("Grid coordinates must be finite one-dimensional arrays")
    if len(result) > 1 and np.any(np.diff(result) <= 0):
        raise ValueError("Grid coordinates must be strictly increasing")
    return result


def attainment_grid(fronts, *, x=None, y=None, max_cells=2_000_000):
    """Exact EAF at grid knots; default knots give every constant step cell.

    probability[j][i] is attained at (x[i], y[j]). For default event knots it
    also applies throughout [x[i],x[i+1]) x [y[j],y[j+1]); the final cells extend
    to positive infinity. Arbitrary supplied knots are exact samples only.
    """
    fronts = run_fronts(fronts, 2)
    all_points = np.vstack(list(fronts.values()))
    xs, ys = _axis(x, all_points, 0), _axis(y, all_points, 1)
    cells = len(xs) * len(ys)
    if cells > integer(max_cells, "max_cells", 1):
        raise ValueError("Exact grid exceeds max_cells; explicitly supply a bounded common grid")
    values = np.empty((len(ys), len(xs)), dtype=float)
    for j, y_value in enumerate(ys):
        queries = np.column_stack((xs, np.full(len(xs), y_value)))
        values[j] = attainment_probability(fronts, queries)
    return {"run_count": len(fronts), "x": xs.tolist(), "y": ys.tolist(),
            "probability": values.tolist(), "exact_step_cells": x is None and y is None,
            "orientation": "probability[y_index][x_index]; weak minimization dominance"}


def attainment_boundary(fronts, *, level=0.5):
    """Exact mathematical boundary of EAF >= level, as nondominated corners.

    This function does not plot. Production displays must use eaf_report,
    which suppresses boundaries when fewer than five paired seeds are present.
    """
    fronts = run_fronts(fronts, 2)
    level = finite(level, "level")
    if not 0 < level <= 1:
        raise ValueError("Attainment level must be in (0, 1]")
    required = ceil(Fraction(str(level)) * len(fronts))
    xs = np.unique(np.vstack(list(fronts.values()))[:, 0])
    corners, best_y = [], float("inf")
    for x_value in xs:
        run_heights = []
        for front in fronts.values():
            active = front[front[:, 0] <= x_value, 1]
            run_heights.append(float(active.min()) if len(active) else float("inf"))
        y_value = sorted(run_heights)[required - 1]
        if y_value < best_y:
            corners.append([float(x_value), y_value])
            best_y = y_value
    vertices = []
    for corner in corners:
        if vertices:
            vertices.append([corner[0], vertices[-1][1]])
        vertices.append(corner)
    return {"level": level, "required_runs": required, "run_count": len(fronts),
            "corners": corners, "step_vertices": vertices,
            "tails": "First corner extends upward; last corner extends rightward"}


def eaf_report(fronts, *, include_grid=False):
    """Pilot presentation guard: no 50% boundary/plot below five seeds."""
    fronts = run_fronts(fronts, 2)
    result = {"run_count": len(fronts), "level": 0.5,
              "point_counts": {key: len(front) for key, front in fronts.items()},
              "eligible_for_plot": len(fronts) >= 5, "boundary": None, "grid": None}
    if len(fronts) < 5:
        result["status"] = "SUPPRESSED_FEWER_THAN_5_SEEDS"
        result["reason"] = "At three seeds report raw pairs; do not draw a 50% EAF plot"
        return result
    result["status"] = "AVAILABLE_DESCRIPTIVE_EAF"
    result["boundary"] = attainment_boundary(fronts)
    if include_grid:
        result["grid"] = attainment_grid(fronts)
    return result


def fixed_quartile_thresholds(reference, *, condition_axis, online=False, current_step=None):
    """Compute q25/q50/q75 once from the shared reference; freeze for all arms.

    The caller supplies coordinates in the same frozen normalized scale as the
    fronts. NumPy's linear sample quantile convention is used explicitly.
    """
    axis = integer(condition_axis, "condition_axis")
    if axis > 2:
        raise ValueError("condition_axis must be 0, 1 or 2")
    front = reference_points(reference, online=online, current_step=current_step)
    values = np.quantile(front[:, axis], [0.25, 0.5, 0.75], method="linear")
    return dict(zip(("q25", "q50", "q75"), map(float, values)))


def conditional_eaf_slices(fronts, *, condition_axis, thresholds, include_grid=False):
    """Exact 3D EAF sections at a fixed third-coordinate threshold.

    Keep points with condition coordinate <= threshold, then project the other
    two coordinates. These are cumulative conditional sections, not quartile
    bins or unconstrained pairwise projections. Preserve all run denominators.
    """
    fronts = run_fronts(fronts, 3)
    axis = integer(condition_axis, "condition_axis")
    if axis > 2:
        raise ValueError("condition_axis must be 0, 1 or 2")
    if set(thresholds) != {"q25", "q50", "q75"}:
        raise ValueError("Supply all three frozen quartile thresholds")
    limits = [finite(thresholds[name], name) for name in ("q25", "q50", "q75")]
    if limits != sorted(limits):
        raise ValueError("Quartile thresholds must be nondecreasing")
    shown_axes = [index for index in range(3) if index != axis]
    result = {"condition_axis": axis, "display_axes": shown_axes,
              "condition": "objective[condition_axis] <= frozen threshold", "slices": {}}
    for name, limit in zip(("q25", "q50", "q75"), limits):
        projected = {key: front[front[:, axis] <= limit][:, shown_axes] for key, front in fronts.items()}
        result["slices"][name] = {"threshold": limit, **eaf_report(projected, include_grid=include_grid)}
    return result

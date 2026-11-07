"""Independent saved-front checks, with a different-axis rectangular HV sweep."""
import numpy as np


def grid_hv(points, reference):
    points = np.asarray(points, dtype=float).reshape(-1, 3)
    points = points[np.all(points < reference, axis=1)]
    if not len(points):
        return 0.0
    zs = np.unique(points[:, 2])
    volume = 0.0
    for bottom, top in zip(zs, np.r_[zs[1:], reference]):
        active = points[points[:, 2] <= bottom]
        active = active[np.argsort(active[:, 0])]
        heights = reference - np.minimum.accumulate(active[:, 1])
        widths = np.diff(np.r_[active[:, 0], reference])
        volume += (top - bottom) * float(np.dot(widths, heights))
    return volume


def coverage(first, second):
    a, b = np.asarray(first), np.asarray(second)
    return float(np.all(a[:, None, :] <= b[None, :, :], axis=2).any(axis=0).mean())


def front_diagnostics(candidate, external, scale):
    a, b = np.asarray(candidate) / scale, np.asarray(external) / scale
    row = {"candidate_points": len(a), "NSGA2_points": len(b),
           "C_NSGA2_candidate": coverage(b, a), "C_candidate_NSGA2": coverage(a, b)}
    for k, name in enumerate(["Cmax", "TEC", "TWC"]):
        row[name + "_best_candidate_vs_NSGA2_percent"] = float(100 * (a[:, k].min() / b[:, k].min() - 1))
    return row

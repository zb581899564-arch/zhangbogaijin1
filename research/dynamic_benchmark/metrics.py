"""Exact minimization HV in three dimensions and empirical IGD+. No adaptive bounds."""
import numpy as np


def nondominated(points):
    points = np.unique(np.asarray(points, dtype=float).reshape(-1, 3), axis=0)
    if not np.isfinite(points).all():
        raise ValueError("Nonfinite objectives")
    # Lexicographic x order means later points cannot dominate earlier survivors.
    keep = []
    for point in points:
        if keep and np.any(np.all(np.asarray(keep) <= point, axis=1)):
            continue
        keep.append(point)
    return np.asarray(keep, dtype=float).reshape(-1, 3)


def _area_2d(points, reference):
    order = np.argsort(points[:, 0], kind="stable")
    area, best = 0., reference[1]
    for y, z in points[order]:
        if z < best:
            area += (reference[0] - y) * (best - z)
            best = z
    return float(area)


def hypervolume(points, reference=(1.1, 1.1, 1.1)):
    reference = np.asarray(reference)
    points = np.asarray(points, dtype=float).reshape(-1, 3)
    points = nondominated(points[np.all(points < reference, axis=1)])
    if not len(points):
        return 0.
    xs = np.unique(points[:, 0])
    volume = 0.
    for i, x in enumerate(xs):
        right = xs[i+1] if i+1 < len(xs) else reference[0]
        volume += (right-x) * _area_2d(points[points[:, 0] <= x, 1:], reference[1:])
    return float(volume)


def igd_plus(front, reference):
    front = np.asarray(front, dtype=float).reshape(-1, 3)
    reference = np.asarray(reference, dtype=float).reshape(-1, 3)
    if not len(front):
        return float("inf")
    if not len(reference):
        raise ValueError("Empty empirical reference")
    total = 0.
    for start in range(0, len(reference), 128):
        delta = np.maximum(front[None, :, :] - reference[start:start+128, None, :], 0.)
        total += np.sqrt((delta**2).sum(axis=2)).min(axis=1).sum()
    return float(total / len(reference))


def check_metrics():
    from itertools import combinations
    points = np.array([[.2,.7,.5],[.5,.2,.4],[.3,.4,.8]])
    exact = 0.
    for n in range(1, 4):
        for group in combinations(points, n):
            exact += (-1)**(n+1) * np.prod(1-np.max(group, axis=0))
    assert abs(hypervolume(points, [1,1,1])-exact) < 1e-12
    assert igd_plus([[.2,.2,.2]], [[.3,.3,.3]]) == 0
    assert abs(igd_plus([[.4,.4,.4]], [[.3,.3,.3]])-np.sqrt(.03)) < 1e-12
    assert len(nondominated([[1,1,1],[2,2,2],[1,1,1]])) == 1

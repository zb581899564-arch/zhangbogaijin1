"""Shared normalization and reference provenance; existing exact indicators."""
from dataclasses import dataclass

import numpy as np

from research.dynamic_benchmark.metrics import hypervolume as _hypervolume
from research.dynamic_benchmark.metrics import igd_plus as _igd_plus
from research.dynamic_benchmark.metrics import nondominated
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage

from .validation import finite, label, points, run_fronts, vector


@dataclass(frozen=True)
class ObjectiveScale:
    """Pre-frozen affine bounds; never estimate bounds from compared fronts."""
    lower: tuple
    upper: tuple

    def __post_init__(self):
        lower, upper = vector(self.lower), vector(self.upper)
        if np.any(upper <= lower):
            raise ValueError("Every upper bound must exceed its lower bound")
        object.__setattr__(self, "lower", tuple(lower))
        object.__setattr__(self, "upper", tuple(upper))

    def normalize(self, front):
        return (points(front) - self.lower) / (np.asarray(self.upper) - self.lower)


@dataclass(frozen=True)
class ReferenceSet:
    """Objective coordinates plus when their use is permitted.

    Caller must truthfully supply provenance and availability. Final-front
    unions are offline-only, even when a current step is supplied.
    """
    objectives: tuple
    source_ids: tuple
    offline_only: bool = True
    available_at: float | None = None

    def __post_init__(self):
        array = points(self.objectives, allow_empty=False)
        sources = tuple(label(item, "reference source") for item in self.source_ids)
        if not sources or len(set(sources)) != len(sources):
            raise ValueError("Reference sources must be present and unique")
        if type(self.offline_only) is not bool:
            raise ValueError("offline_only must be a boolean")
        if not self.offline_only and self.available_at is None:
            raise ValueError("Online reference needs a frozen availability step")
        if self.available_at is not None:
            at = finite(self.available_at, "available_at")
            if at < 0:
                raise ValueError("available_at must be nonnegative")
            object.__setattr__(self, "available_at", at)
        object.__setattr__(self, "objectives", tuple(map(tuple, array)))
        object.__setattr__(self, "source_ids", sources)


def shared_final_reference(final_fronts, *, online=False):
    """One nondominated union over all registered final fronts for one instance."""
    if online:
        raise ValueError("A final-front union must never guide online search")
    fronts = run_fronts(final_fronts, 3)
    if any(not len(front) for front in fronts.values()):
        raise ValueError("Missing/empty final runs must be reported before reference construction")
    union = nondominated(np.vstack(list(fronts.values())))
    return ReferenceSet(tuple(map(tuple, union)), tuple(fronts))


def reference_points(reference, *, online=False, current_step=None):
    if isinstance(reference, ReferenceSet):
        if online:
            if reference.offline_only:
                raise ValueError("Final-front empirical reference is offline-only")
            if current_step is None or finite(current_step, "current_step") < reference.available_at:
                raise ValueError("Reference is not available at this online step")
        return points(reference.objectives, allow_empty=False)
    if online:
        raise ValueError("Online reference requires explicit provenance and availability")
    return points(reference, allow_empty=False)


def igd(front, reference, *, online=False, current_step=None):
    """Conventional IGD: mean over reference of nearest Euclidean front distance."""
    front = points(front)
    reference = reference_points(reference, online=online, current_step=current_step)
    if not len(front):
        return float("inf")
    total = 0.0
    for start in range(0, len(reference), 128):
        delta = front[None, :, :] - reference[start:start + 128, None, :]
        total += np.linalg.norm(delta, axis=2).min(axis=1).sum()
    return float(total / len(reference))


def igd_plus(front, reference, *, online=False, current_step=None):
    reference = reference_points(reference, online=online, current_step=current_step)
    return _igd_plus(points(front), reference)


def hypervolume(front, reference):
    """Existing exact 3D HV, with explicit finite shape checks and no clipping."""
    return _hypervolume(points(front), vector(reference))


def objective_extremes(front, scale):
    """All tied objective minimizers as complete raw and normalized vectors."""
    front = np.unique(points(front, allow_empty=False), axis=0)
    normalized = scale.normalize(front)
    result = {}
    for axis, name in enumerate(("Cmax", "TEC", "TWC")):
        tied = front[:, axis] == front[:, axis].min()
        result[name] = {"axis": axis, "normalized_minimum": float(normalized[tied, axis][0]),
                        "raw_vectors": front[tied].tolist(),
                        "normalized_vectors": normalized[tied].tolist(),
                        "tie_count": int(tied.sum())}
    return result


def evaluate_front(front, empirical_reference, scale, hv_reference, *, online=False, current_step=None):
    raw_reference = reference_points(empirical_reference, online=online, current_step=current_step)
    normalized, normalized_reference = scale.normalize(front), scale.normalize(raw_reference)
    return {"HV": hypervolume(normalized, hv_reference),
            "IGDplus": igd_plus(normalized, normalized_reference),
            "IGD": igd(normalized, normalized_reference),
            "extremes": objective_extremes(front, scale)}


def exact_coverage(candidate, control):
    """Exact weak dominance, both directions, equality counted in both."""
    return bidirectional_coverage(points(candidate), points(control))

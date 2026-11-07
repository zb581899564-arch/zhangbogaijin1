"""Accepted indicator APIs, frozen scales, descriptive within-instance pairs."""
from statistics import median
import numpy as np

from research.pilot_evaluation import (exact_coverage, igd, igd_plus,
                                     igd_plus_symmetric_effect, shared_final_reference)
from research.dynamic_benchmark.metrics import nondominated
from analysis_common import COMPARISONS, REFERENCES, require


class FrozenScale:
    def __init__(self, lower, width):
        self.lower, self.width = lower, width

    def normalize(self, front):
        return (np.asarray(front, dtype=float) - self.lower) / self.width


def frozen_scale(spec):
    norm = spec["normalization"]
    lower, width = np.asarray(norm["lower"], float), np.asarray(norm["scale"], float)
    require(lower.shape == width.shape == (3,) and np.isfinite(lower).all()
            and np.isfinite(width).all() and (width > 0).all(), "Invalid frozen normalization")
    return FrozenScale(lower, width)


def hv(front, reference):
    import moocore
    points = np.asarray(front, float).reshape(-1, 3)
    points = points[np.all(points < reference, axis=1)]
    return float(moocore.hypervolume(points, ref=[reference] * 3)) if len(points) else 0.0


def metrics(front, empirical_reference, scale):
    front = nondominated(front)
    require(len(front) > 0, "An empty front cannot enter joint metric comparisons")
    normalized, reference = scale.normalize(front), scale.normalize(empirical_reference)
    return dict(front=front.tolist(), frontSize=len(front),
                HV={str(r): hv(normalized, r) for r in REFERENCES},
                IGDplus=igd_plus(normalized, reference), IGD=igd(normalized, reference),
                objectiveMinimum=front.min(axis=0).tolist(),
                objectiveMinimumVectors={name: front[int(np.argmin(front[:, index]))].tolist()
                    for index, name in enumerate(("Cmax", "TEC", "TWC"))})


def reference_from(fronts):
    reference = shared_final_reference({f"{seed}/{arm}": front for (seed, arm), front in fronts.items()})
    return np.asarray(reference.objectives), list(reference.source_ids)


def distribution(values, *, higher=True):
    require(bool(values), "No paired values")
    signed = [v if higher else -v for v in values]
    return dict(median=float(median(values)), range=[float(min(values)), float(max(values))],
                wins=sum(v > 0 for v in signed), ties=sum(v == 0 for v in signed),
                losses=sum(v < 0 for v in signed), tieTolerance=0.0)


def pair(seed, candidate, control):
    a, b = candidate, control
    coverage = exact_coverage(a["front"], b["front"])
    effects = {r: (100.0 * (a["HV"][r] / b["HV"][r] - 1.0)
                   if b["HV"][r] > 0 else None) for r in a["HV"]}
    return dict(seed=seed, HVEffectPct=effects,
                HVAbsoluteDifference={r: a["HV"][r] - b["HV"][r] for r in a["HV"]},
                IGDplusSymmetricImprovementPct=100 * igd_plus_symmetric_effect(a["IGDplus"], b["IGDplus"]),
                IGDplusImprovement=b["IGDplus"] - a["IGDplus"],
                IGDImprovement=b["IGD"] - a["IGD"], coverage=coverage,
                Cdelta=coverage["C_A_B"] - coverage["C_B_A"])


def compare(observations, seeds, endpoint):
    values = {(row["seed"], row["arm"]): row[endpoint] for row in observations}
    result = []
    for candidate, control in COMPARISONS:
        pairs = [pair(seed, values[seed, candidate], values[seed, control]) for seed in seeds]
        percent = {}
        for r in map(str, REFERENCES):
            entries = [p["HVEffectPct"][r] for p in pairs]
            percent[r] = distribution(entries) if None not in entries else {
                "available": False, "reason": "Zero control HV; use absolute differences"}
        result.append(dict(candidate=candidate, control=control, endpoint=endpoint, pairs=pairs,
            HVEffectPct=percent,
            HVAbsoluteDifference={r: distribution([p["HVAbsoluteDifference"][r] for p in pairs])
                                  for r in map(str, REFERENCES)},
            IGDplusSymmetricImprovementPct=distribution([p["IGDplusSymmetricImprovementPct"] for p in pairs]),
            IGDplusImprovement=distribution([p["IGDplusImprovement"] for p in pairs]),
            IGDImprovement=distribution([p["IGDImprovement"] for p in pairs]),
            Cdelta=distribution([p["Cdelta"] for p in pairs]),
            interpretation=("S incremental over global G supply" if (candidate, control) == ("UNION", "G")
                            else "G incremental over S supply" if (candidate, control) == ("UNION", "S")
                            else "Descriptive paired donor-pool comparison")))
    return result


def gain_metrics(final, background, receipt):
    count, seconds = receipt["successful"], receipt["searchSeconds"]
    delta = {r: final["HV"][r] - background["HV"][r] for r in final["HV"]}
    require(min(delta.values()) >= -1e-11, "Archive HV decreased from its common paid A0")
    return dict(HVAboveA0=delta,
                HVAboveA0PerNewFE={r: value / count for r, value in delta.items()},
                HVAboveA0PerSearchSecond={r: value / seconds if seconds > 0 else None for r, value in delta.items()},
                interpretation="Descriptive efficiency of this complete pass; no equal-time comparison")

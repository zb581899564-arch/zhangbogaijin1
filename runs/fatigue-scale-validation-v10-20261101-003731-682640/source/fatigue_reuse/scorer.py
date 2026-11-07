"""Parent-bound score cache; chain owns invalidation and usage accounting."""
from dataclasses import dataclass
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.adjoint import adjoint
from research.fatigue_mechanism.prediction import prepare_defects, score_defects
from research.fatigue_topology.counterfactual import boundary_costates
from .stage0 import exact_stage0


@dataclass
class ScoreCache:
    genome: object
    version: int
    method: str
    pullback: object
    effective: np.ndarray
    old_direct: np.ndarray
    arrays: tuple
    uses: int = 0


def build(instance, params, genome, parent, method, weights, scales, version):
    effective = np.asarray(weights) / scales
    # v2 boundary routine divides by parent objectives; preserve INITIAL scales.
    adjusted_weights = effective * parent.objectives
    if method.startswith("cut_"):
        pullback = boundary_costates(instance, params, parent, adjusted_weights, method == "cut_fatigue")
        old_direct = np.array([0., sum(o.energy for o in parent.operations[:instance.jobs]),
                               sum(o.labor for o in parent.operations[:instance.jobs])])
        arrays = params.arrays(instance)
    else:
        pullback = adjoint(parent, instance, params, weights, scales, include_fatigue=False)
        old_direct, arrays = np.zeros(3), ()
    return ScoreCache(genome, version, method, pullback, effective, old_direct, arrays)


def scores(instance, params, genome, parent, pool, cache, version):
    if cache.genome != genome or cache.version != version:
        raise AssertionError("stale adjoint cache")
    cache.uses += 1
    if cache.method == "local_time":
        return score_defects(prepare_defects(instance, params, parent, pool), cache.pullback), 0, 0
    predictions, stage0_ns = [], 0
    for candidate in pool:
        started = perf_counter_ns()
        first = exact_stage0(instance, candidate.genome, cache.arrays)
        stage0_ns += perf_counter_ns() - started
        state_delta = np.column_stack((first.C - parent.C[:instance.jobs], first.v - parent.v[:instance.jobs]))
        predictions.append(float((first.direct - cache.old_direct) @ cache.effective
                                  + np.sum(cache.pullback * state_delta)))
    return np.asarray(predictions), len(pool), stage0_ns

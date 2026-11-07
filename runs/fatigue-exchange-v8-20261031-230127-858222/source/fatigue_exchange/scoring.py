"""Reuse validated boundary engines, no new fatigue score or migration cache."""
import numpy as np
from research.fatigue_reuse import scorer
from research.fatigue_mechanism.prediction import prepare_defects, score_defects


def build(instance, params, state, parent, method, scales, version):
    name = {"pool_cheap": "local_time", "pool_time": "cut_time", "pool_fatigue": "cut_fatigue"}[method]
    return scorer.build(instance, params, state.genome(), parent, name, [0., 1., 0.], scales, version)


def scores(instance, params, state, parent, candidates, cache, method, version):
    if method == "pool_cheap":
        if cache.genome != state.genome() or cache.version != version:
            raise AssertionError("stale scoring cache")
        cache.uses += 1
        defects = prepare_defects(instance, params, parent, candidates, max_affected=instance.jobs)
        return score_defects(defects, cache.pullback), 0, 0
    values, calls, elapsed = scorer.scores(instance, params, state.genome(), parent, candidates, cache, version)
    return np.asarray(values), calls, elapsed

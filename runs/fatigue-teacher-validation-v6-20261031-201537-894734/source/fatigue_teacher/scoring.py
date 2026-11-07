"""Four selector rules sharing a legal pool; only receiver information differs."""
import numpy as np
from research.fatigue_mechanism.prediction import prepare_defects, score_defects
from research.fatigue_reuse import scorer as full
from research.fatigue_incremental import scorer as incremental


def build(instance, params, genome, parent, method, regime, weights, scales, version):
    if method in ("direct", "random"):
        return None
    name = "local_time" if method == "cheap" else "cut_"+method
    engine = incremental if regime == "fixed_FA" and method != "cheap" else full
    return engine.build(instance, params, genome, parent, name, weights, scales, version)


def scores(instance, params, genome, parent, pool, teachers, cache, method, regime, version):
    if method == "random":
        return None, 0, 0
    if method == "direct":
        quality = {t.bank_index: t.value for t in teachers}
        return np.asarray([min((quality[i] for i, _ in c.origins), default=0.) for c in pool]), 0, 0
    if method == "cheap":
        if cache.genome != genome or cache.version != version:
            raise AssertionError("stale receiver cache")
        cache.uses += 1
        defects = prepare_defects(instance, params, parent, pool, max_affected=instance.jobs)
        return score_defects(defects, cache.pullback), 0, 0
    engine = incremental if regime == "fixed_FA" else full
    return engine.scores(instance, params, genome, parent, pool, cache, version)

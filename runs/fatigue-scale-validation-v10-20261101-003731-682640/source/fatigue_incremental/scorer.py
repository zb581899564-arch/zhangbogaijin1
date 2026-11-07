"""Same boundary scores as v3, with exact suffix reuse and measured work."""
from dataclasses import dataclass
from time import perf_counter_ns
import numpy as np
from research.fatigue_reuse import scorer as full_scorer
from .prefix import build_prefix, incremental_stage0


@dataclass
class IncrementalCache:
    base: object
    prefix: object
    work: dict


def build(instance, params, genome, parent, method, weights, scales, version):
    base = full_scorer.build(instance, params, genome, parent, method, weights, scales, version)
    if method == "local_time":
        return base
    prefix = build_prefix(instance, genome, parent)
    work = {"candidate_evaluations": 0, "equivalent_full_ops": 0, "recomputed_ops": 0,
            "reused_prefix_ops": 0, "unchanged_factory_ops": 0, "affected_factory_visits": 0,
            "checkpoint_positions": sum(len(f.tokens) + 1 for f in prefix.factories)}
    return IncrementalCache(base, prefix, work)


def scores(instance, params, genome, parent, pool, cache, version):
    if not isinstance(cache, IncrementalCache):
        return full_scorer.scores(instance, params, genome, parent, pool, cache, version)
    base = cache.base
    if base.genome != genome or base.version != version:
        raise AssertionError("stale incremental cache")
    base.uses += 1
    predictions, stage0_ns = [], 0
    for candidate in pool:
        start = perf_counter_ns()
        first, work = incremental_stage0(instance, candidate.genome, base.arrays, cache.prefix)
        stage0_ns += perf_counter_ns() - start
        for name, value in work.items():
            cache.work[name] += value
        cache.work["candidate_evaluations"] += 1
        cache.work["equivalent_full_ops"] += instance.jobs
        state_delta = np.column_stack((first.C - parent.C[:instance.jobs], first.v - parent.v[:instance.jobs]))
        predictions.append(float((first.direct - base.old_direct) @ base.effective
                                  + np.sum(base.pullback * state_delta)))
    return np.asarray(predictions), len(pool), stage0_ns

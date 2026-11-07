"""Component timing, independent of candidate truth and of selection metrics."""
from __future__ import annotations

from collections import Counter
from time import perf_counter_ns
import numpy as np
from .adjoint import adjoint
from .decoder import decode
from .prediction import prepare_defects, score_defects
from .statistics import select_minima


class DecodeCounter:
    def __init__(self):
        self.calls = Counter()

    def evaluate(self, purpose, *args, **kwargs):
        self.calls[purpose] += 1
        return decode(*args, **kwargs)


def measure(function, repeats):
    function()  # explicit warm-up, included in DecodeCounter if a full decode
    values = []
    for _ in range(repeats):
        start = perf_counter_ns()
        function()
        values.append((perf_counter_ns() - start) / 1e6)
    return {"median_ms": float(np.median(values)), "samples_ms": values, "warmups": 1}


def common_timings(counter, instance, params, genome, trace, pool, pool_factory, repeats):
    result = {
        "plain_decode": measure(lambda: counter.evaluate("timing_plain", instance, genome, params, retain_trace=False), repeats),
        "trace_decode": measure(lambda: counter.evaluate("timing_trace", instance, genome, params), repeats),
        "pool_generation": measure(pool_factory, repeats),
        "defects": measure(lambda: prepare_defects(instance, params, trace, pool), repeats),
    }
    rng = np.random.default_rng(8675309)
    result["random_choice"] = measure(lambda: rng.integers(len(pool)), repeats)
    return result


def target_timings(instance, params, trace, defects, weights, scales, full, time_only, scores, repeats):
    result = {}
    rng = np.random.default_rng(8675309)
    for method, reverse, include_fatigue in (("fatigue_adjoint", full, True), ("time_only", time_only, False)):
        result[method] = {
            "adjoint": measure(lambda: adjoint(trace, instance, params, weights, scales, include_fatigue), repeats),
            "combine": measure(lambda: score_defects(defects, reverse), repeats),
            "choice": measure(lambda: rng.choice(select_minima(scores[method])), repeats),
        }
    return result


def cost_proxies(common, target):
    median = lambda key: common[key]["median_ms"]
    random = 2 * median("plain_decode") + median("pool_generation") + median("random_choice")
    result = {"random": random}
    for method, parts in target.items():
        guide = median("defects") + sum(part["median_ms"] for part in parts.values())
        result[method] = 2 * median("trace_decode") + median("pool_generation") + guide
        result[method + "_guidance_ms"] = guide
        result[method + "_guidance_in_plain_decodes"] = guide / median("plain_decode")
        result[method + "_cost_over_random"] = result[method] / random
    result["trace_over_plain"] = median("trace_decode") / median("plain_decode")
    return result

"""Charge actual calls and expose unchanged-parent amortization assumptions."""
from collections import Counter
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.adjoint import adjoint
from research.fatigue_mechanism.prediction import score_defects
from research.fatigue_mechanism.statistics import select_minima
from research.fatigue_mechanism.timing import measure
from .counterfactual import stage0, fixed_later
from .scoring import prepare


class Accounting:
    def __init__(self):
        self.calls = Counter()

    def adaptive(self, purpose, *args, **kwargs):
        self.calls[purpose] += 1
        return decode(*args, **kwargs)

    def first(self, *args):
        self.calls["diagnostic_stage0"] += 1
        return stage0(*args)

    def fixed(self, *args):
        self.calls["diagnostic_fixed_later"] += 1
        return fixed_later(*args)


def case_timing(counter, instance, params, genome, trace, targets, repeats):
    common = {
        "plain": measure(lambda: counter.adaptive("timing_plain", instance, genome, params, False), repeats),
        "trace": measure(lambda: counter.adaptive("timing_trace", instance, genome, params), repeats),
        "adjoints": {},
    }
    for target, weights in targets.items():
        common["adjoints"][target] = {}
        for method, fatigue in (("fatigue_adjoint", True), ("time_only", False)):
            common["adjoints"][target][method] = measure(
                lambda: adjoint(trace, instance, params, weights, trace.objectives, fatigue), repeats)
    return common


def pool_timing(instance, params, trace, pool, factory, defects, reverse, scores, repeats):
    rng = np.random.default_rng(8675309)
    result = {"generation": measure(factory, repeats),
              "defects": measure(lambda: prepare(instance, params, trace, pool), repeats),
              "random_choice": measure(lambda: rng.integers(len(pool)), repeats), "targets": {}}
    for target, pullbacks in reverse.items():
        result["targets"][target] = {}
        for method in ("fatigue_adjoint", "time_only"):
            result["targets"][target][method] = measure(
                lambda: rng.choice(select_minima(score_defects(defects, pullbacks[method]))), repeats)
    return result


def cost_proxy(common, pool, target, method, q):
    t = lambda name: common[name]["median_ms"]
    generation = pool["generation"]["median_ms"]
    if method == "random":
        return t("plain") / q + generation + pool["random_choice"]["median_ms"] + t("plain")
    setup = t("trace") + common["adjoints"][target][method]["median_ms"]
    variable = pool["defects"]["median_ms"] + pool["targets"][target][method]["median_ms"]
    return setup / q + generation + variable + t("trace")

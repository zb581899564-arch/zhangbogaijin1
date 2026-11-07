"""One pool's predictions precede adaptive and frozen-route observations."""
from dataclasses import asdict
import numpy as np
from research.fatigue_mechanism.statistics import selection_metrics
from research.fatigue_mechanism.validation import validate_schedule
from .counterfactual import cut_prediction
from .diagnostics import regime, error_terms
from .scoring import prepare, predictions
from .trials import trial_instance
from .timing import pool_timing, cost_proxy


def observe_trial(counter, instance, params, parent, trial, reverse, scores, index, identity, protocol):
    changed = trial_instance(instance, trial)
    first = counter.first(changed, trial.genome, params)
    fixed = counter.fixed(changed, params, first, parent)
    truth = counter.adaptive("offline_adaptive_truth", changed, trial.genome, params)
    fixed_check = validate_schedule(changed, params, fixed)
    truth_check = validate_schedule(changed, params, truth)
    np.testing.assert_allclose(first.C[:instance.jobs], truth.C[:instance.jobs], atol=1e-10, rtol=1e-12)
    observed = regime(parent, truth, instance.jobs)
    frozen_regime = regime(parent, fixed, instance.jobs)
    if observed["later_graph_changed_ops"] == 0:
        np.testing.assert_allclose(fixed.objectives, truth.objectives, atol=1e-8, rtol=1e-12)
    targets = {}
    for target, weights in protocol["targets"].items():
        effective = np.asarray(weights) / parent.objectives
        actual = float((truth.objectives - parent.objectives) @ effective)
        frozen = float((fixed.objectives - parent.objectives) @ effective)
        cut = cut_prediction(instance, parent, first, weights, reverse[target]["cut"])
        cheap = scores[target]["scores"]["fatigue_adjoint"][index]
        targets[target] = {"actual": actual, "fixed": frozen, "cut": cut,
                           "scores": {m: s[index] for m, s in scores[target]["scores"].items()},
                           "components": error_terms(cheap, cut, frozen, actual)}
        if scores[target]["tangents"] is not None:
            targets[target]["tangents"] = {m: s[index] for m, s in scores[target]["tangents"].items()}
    return {**identity, "index": index, "trial": asdict(trial), "regime": observed,
            "fixed_regime": frozen_regime, "truth_objectives": truth.objectives.tolist(),
            "fixed_objectives": fixed.objectives.tolist(), "targets": targets,
            "truth_validation": truth_check, "fixed_validation": fixed_check}


def run_pool(counter, instance, params, parent, pool, factory, reverse, identity, protocol, common_time, emit):
    defects = prepare(instance, params, parent, pool)
    scores = predictions(instance, parent, pool, defects, reverse)
    emit("predictions", {**identity, "targets": scores, "parent_objectives": parent.objectives.tolist(),
                         "random_support": list(range(len(pool)))})
    observations = []
    for index, trial in enumerate(pool):
        observation = observe_trial(counter, instance, params, parent, trial, reverse, scores,
                                    index, identity, protocol)
        observations.append(observation)
        emit("observations", observation)
    timing = pool_timing(instance, params, parent, pool, factory, defects, reverse, scores, protocol["timing_repeats"])
    emit("timing", {**identity, "scope": "pool", "values": timing})
    selections = []
    for target in protocol["targets"]:
        actual = np.array([row["targets"][target]["actual"] for row in observations])
        for method in ("fatigue_adjoint", "time_only", "random"):
            metrics = selection_metrics(scores[target]["scores"].get(method), actual)
            assert metrics["tie_indices"] == scores[target]["ties"].get(method, list(range(len(pool))))
            costs = {q: cost_proxy(common_time, timing, target, method, q)
                     for q in protocol["cache_pools_per_unchanged_parent"]}
            row = {**identity, "target": target, "method": method, **metrics,
                   "cost_ms_by_q": costs, "rate_by_q": {q: metrics["accepted_gain"] / c for q, c in costs.items()}}
            selections.append(row)
            emit("selections", row)
    return observations, selections

"""One frozen parent/pool: predict first, evaluate truth second, time separately."""
from __future__ import annotations

from dataclasses import asdict
import numpy as np
from .adjoint import adjoint
from .prediction import prepare_defects, score_defects
from .statistics import select_minima, selection_metrics
from .timing import common_timings, target_timings, cost_proxies
from .validation import validate_schedule


def predict_targets(instance, params, trace, defects, targets):
    output = {}
    for target, weights in targets.items():
        full = adjoint(trace, instance, params, weights, trace.objectives)
        control = adjoint(trace, instance, params, weights, trace.objectives, include_fatigue=False)
        scores = {"fatigue_adjoint": score_defects(defects, full), "time_only": score_defects(defects, control)}
        ties = {method: select_minima(values).tolist() for method, values in scores.items()}
        output[target] = {"scores": scores, "ties": ties, "full": full, "control": control}
    return output


def topology_diagnostics(parent, child, jobs):
    topology, later, branch = 0, 0, 0
    for old, new in zip(parent.operations, child.operations):
        changed = (old.factory, old.machine_id, old.worker_id, old.parents) != (new.factory, new.machine_id, new.worker_id, new.parents)
        topology += changed
        later += changed and old.op_id >= jobs
        branch += old.parents[old.active_branch] != new.parents[new.active_branch]
    return {"topology_changed_ops": topology, "later_topology_changed_ops": later,
            "active_parent_changed_ops": branch,
            "cmax_sink_changed": min(parent.makespan_ties) != min(child.makespan_ties)}


def run_case(counter, instance, params, parent, pool, pool_factory, identity, protocol, emit):
    trace = counter.evaluate("parent_for_prediction", instance, parent, params)
    parent_check = validate_schedule(instance, params, trace)
    defects = prepare_defects(instance, params, trace, pool, protocol["max_direct_defects"])
    predictions = predict_targets(instance, params, trace, defects, protocol["targets"])
    # Write choices BEFORE the oracle evaluation. The selectors cannot read truth.
    emit("predictions", {**identity, "parent_objectives": trace.objectives.tolist(),
         "targets": {t: {"scores": {m: s.tolist() for m, s in p["scores"].items()},
                          "ties": p["ties"], "random_support": list(range(len(pool)))} for t, p in predictions.items()}})
    truths, diagnostics = [], []
    for index, candidate in enumerate(pool):
        child = counter.evaluate("offline_all_candidate_truth", instance, candidate.genome, params)
        check = validate_schedule(instance, params, child)
        diagnostic = topology_diagnostics(trace, child, instance.jobs)
        diagnostics.append(diagnostic)
        truths.append(child.objectives)
        emit("candidates", {**identity, "index": index, "kind": candidate.kind, "jobs": candidate.jobs,
             "genome": asdict(candidate.genome), "objectives": child.objectives.tolist(),
             "delta": (child.objectives - trace.objectives).tolist(), "validation": check,
             "direct_defects": len(defects[index].ids), **diagnostic})
    common = common_timings(counter, instance, params, parent, trace, pool, pool_factory, protocol["timing_repeats"])
    selections, timing = [], {"common": common, "targets": {}}
    for target, weights in protocol["targets"].items():
        p = predictions[target]
        actual_delta = (np.asarray(truths) - trace.objectives) @ (np.asarray(weights) / trace.objectives)
        target_time = target_timings(instance, params, trace, defects, weights, trace.objectives,
                                    p["full"], p["control"], p["scores"], protocol["timing_repeats"])
        proxies = cost_proxies(common, target_time)
        timing["targets"][target] = {"components": target_time, "cost_proxy": proxies}
        for method in protocol["methods"]:
            metrics = selection_metrics(p["scores"].get(method), actual_delta)
            expected_ties = p["ties"].get(method, list(range(len(pool))))
            assert metrics["tie_indices"] == expected_ties, "oracle changed the selection"
            row = {**identity, "target": target, "method": method, **metrics,
                   "cost_proxy_ms": proxies[method],
                   "accepted_gain_per_proxy_ms": metrics["accepted_gain"] / proxies[method]}
            selections.append(row)
            emit("selections", row)
    emit("timing", {**identity, **timing})
    return selections, {**identity, "parent_validation": parent_check,
                        "parent_objectives": trace.objectives.tolist(),
                        "mean_later_topology_changed_ops": float(np.mean([d["later_topology_changed_ops"] for d in diagnostics])),
                        "candidates_with_later_topology_change": sum(d["later_topology_changed_ops"] > 0 for d in diagnostics),
                        "max_direct_defects": max(len(d.ids) for d in defects)}

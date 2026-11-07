"""Full-trace certificates for same-state static/dynamic counterfactuals."""
from dataclasses import asdict
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from .analysis import best_path


def relations(trace, jobs, first, second):
    result = {"worker_adjacent_stages": [], "machine_adjacent_stages": [], "same_worker_stages": []}
    for stage in range(len(trace.operations)//jobs):
        a, b = trace.operations[stage*jobs+first], trace.operations[stage*jobs+second]
        if a.factory == b.factory and a.worker_id == b.worker_id:
            result["same_worker_stages"].append(stage)
        for role, name in ((1, "machine_adjacent_stages"), (2, "worker_adjacent_stages")):
            if a.parents[role] == b.op_id or b.parents[role] == a.op_id:
                result[name].append(stage)
    return result


def dominance(graph, objectives, reference, parent, endpoint, epsilon):
    neighbors = np.unique(graph.destination[graph.row_pointer[parent]:graph.row_pointer[parent+1]])
    scaled = objectives/reference
    delta = scaled[neighbors]-scaled[parent]
    improves = np.all(delta <= epsilon, axis=1) & np.any(delta < -epsilon, axis=1)
    joint = scaled[endpoint]-scaled[parent]
    return {"N1_pareto_improving_neighbors": int(improves.sum()),
            "joint_pareto_dominates_parent": bool(np.all(joint <= epsilon) and np.any(joint < -epsilon))}


def certify(instance, params, graph, tables, C, H, reference, analyses, values,
            target, dynamic, parent, category, counts, epsilon):
    chosen = "beta0" if category == "beta0_only" else dynamic
    first, middle, second, end = best_path(graph, values[chosen, target], analyses[chosen, target], parent)
    assert first != second and middle in graph.neighbors(parent, first) and end in graph.neighbors(middle, second)
    data = []
    for name in ("beta0", dynamic):
        mi = ("beta0", "strong_fast", "strong_slow").index(name)
        traces = []
        for state_id in (parent, middle, end):
            state = graph.space.state(state_id)
            result = decode(instance, state.genome(), params[name])
            validate_schedule(instance, params[name], result)
            np.testing.assert_array_equal(result.objectives, tables[mi, state_id])
            np.testing.assert_array_equal(result.C, C[mi, state_id])
            np.testing.assert_array_equal(result.v, H[mi, state_id])
            traces.append(result)
            counts["witness_full"] += 1
        score = values[name, target]
        data.append({"model": name, "scalar_values": score[[parent, middle, end]],
            "joint_gain": float(score[parent]-score[end]),
            "N1_has_improvement": bool(not analyses[name, target]["N1_local"][parent]),
            "weak": bool(analyses[name, target]["weak"][parent]), "strict": bool(analyses[name, target]["strict"][parent]),
            "parent_relations": relations(traces[0], instance.jobs, first, second),
            **dominance(graph, tables[mi], reference, parent, end, epsilon),
            "traces": [{"objectives": t.objectives, "C": t.C, "fatigue": t.v,
                        "operations": [asdict(o) for o in t.operations]} for t in traces]})
    score = values[chosen, target]
    assert analyses[chosen, target]["strict"][parent]
    assert score[middle] > score[parent]+epsilon and score[end] < score[parent]-epsilon
    return {"target": target, "dynamic_model": dynamic, "category": category,
        "parent": parent, "middle": middle, "endpoint": end, "first_job": first, "second_job": second,
        "genomes": [asdict(graph.space.state(i).genome()) for i in (parent, middle, end)], "models": data}


def make_certificates(instance, params, graph, tables, C, H, reference, analyses, values, records, counts, identity, epsilon):
    for target in ("Cmax", "TEC", "TWC", "balanced"):
        baseline = analyses["beta0", target]["strict"]
        for dynamic in ("strong_fast", "strong_slow"):
            active = analyses[dynamic, target]["strict"]
            masks = {"beta0_only": baseline & ~active, "dynamic_only": active & ~baseline, "both": active & baseline}
            for category, mask in masks.items():
                ids = np.flatnonzero(mask)
                if len(ids):
                    result = certify(instance, params, graph, tables, C, H, reference, analyses, values,
                                     target, dynamic, int(ids[0]), category, counts, epsilon)
                    records.emit("witnesses", {**identity, **result})
                    counts["witnesses"] += 1

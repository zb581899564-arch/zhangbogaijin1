"""Matched conditional panels; ordinary controls pay all real physical calls."""
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from .controls import run_trial, exact_probability
from .space import State
from .protocol import PROTOCOL


def state_from_record(value):
    return State(tuple(tuple(q) for q in value["queues"]), value["resources"])


def run(instance, params, graph, tables, reference, analyses, values, records, counts, identity):
    eligible = np.flatnonzero(np.logical_or.reduce([analyses[m, "TEC"]["weak"] for m in PROTOCOL["models"]]))
    fallback = len(eligible) == 0
    source = np.arange(graph.space.size) if fallback else eligible
    selected = np.sort(np.random.default_rng(20261126+identity["seed"]).choice(source, min(4, len(source)), replace=False))
    records.emit("events", {**identity, "event": "panel_selected", "eligible_states": len(eligible),
                            "fallback_uniform": fallback, "selected": selected})
    for parent in selected:
        state = graph.space.state(int(parent))
        for mi, model in enumerate(PROTOCOL["models"]):
            for method in PROTOCOL["controls"]:
                seed = 20261127+identity["seed"]+1009*int(parent)+mi*10000019
                result = run_trial(instance, params[model], state, PROTOCOL["targets"]["TEC"], reference,
                                   method, seed, PROTOCOL["control_budget"])
                counts["control_parent_full"] += 1
                counts["control_child_full"] += PROTOCOL["control_budget"]
                counts["control_online_ns"] += result["elapsed_ns"]
                started = perf_counter_ns()
                for row in result["rows"]:
                    mid = graph.space.index(state_from_record(row["middle"]))
                    child = graph.space.index(state_from_record(row["child"]))
                    assert mid in graph.neighbors(parent, row["first_job"])
                    if row["second_job"] is not None:
                        assert row["second_job"] != row["first_job"] and child in graph.neighbors(mid, row["second_job"])
                    np.testing.assert_array_equal(row["objectives"], tables[mi, child])
                best = state_from_record(result["best_state"])
                final = decode(instance, best.genome(), params[model])
                np.testing.assert_array_equal(final.objectives, result["best_objectives"])
                validate_schedule(instance, params[model], final)
                counts["control_final_QA_full"] += 1
                counts["control_QA_ns"] += perf_counter_ns()-started
                started = perf_counter_ns()
                probability = exact_probability(graph, values[model, "TEC"], int(parent), method,
                                                result["pairs"], PROTOCOL["epsilon"], PROTOCOL["control_budget"])
                counts["probability_ns"] += perf_counter_ns()-started
                records.emit("controls", {**identity, "parent": int(parent), "model": model,
                    "panel_fallback": fallback, "parent_weak": bool(analyses[model, "TEC"]["weak"][parent]),
                    "parent_strict": bool(analyses[model, "TEC"]["strict"][parent]),
                    **result, "offline_exact_distribution": probability})
                counts["control_trials"] += 1

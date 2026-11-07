"""Fixed experiment across all cases; no table input to the local search."""
from collections import Counter
from time import perf_counter_ns
import traceback
import numpy as np
from research.fatigue_coordination.experiment import checked_graph
from research.fatigue_coordination.panels import state_from_record
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from .protocol import PROTOCOL
from .records import Records, save
from .artifacts import create
from . import cases, coverage
from .chain import run as run_chain


def verify(instance, params, result, counts):
    started = perf_counter_ns()
    final = decode(instance, state_from_record(result["final_state"]).genome(), params)
    np.testing.assert_array_equal(final.objectives, result["final_objectives"])
    validate_schedule(instance, params, final)
    counts["search_QA_full"] += 1
    counts["search_QA_ns"] += perf_counter_ns()-started


def block(instance, params, state, identity, records, counts):
    seed = identity["search_seed"]+identity["instance_seed"]*17+identity["parent"]*1009
    for mode, seconds in (("FE", None), ("time", .02), ("time", .08)):
        scheduling = np.random.default_rng(seed+731*PROTOCOL["models"].index(identity["model"])+int((seconds or 0)*1e9))
        for method in scheduling.permutation(PROTOCOL["methods"]):
            result = run_chain(instance, params, state, str(method), seed, mode, seconds)
            counts["search_full"] += result["full_decodes"]
            counts["search_online_ns"] += result["elapsed_ns"]
            counts["search_runs"] += 1
            verify(instance, params, result, counts)
            records.emit("search", {**identity, **result})


def run(project):
    started, counts = perf_counter_ns(), Counter()
    output = create(project)
    counts["snapshot_source_ns"] = perf_counter_ns()-started
    records, active = Records(output), None
    print(f"RUN_DIRECTORY {output}", flush=True)
    try:
        graph = checked_graph(4, output, counts)
        for number, identity in enumerate(cases.configurations(), 1):
            active = identity
            instance, params, tables, reference, analyses = cases.load(project, output, graph, identity, records, counts)
            begin = perf_counter_ns()
            eligible = coverage.evaluate(graph, tables, reference, analyses, identity, records.emit)
            counts["coverage_ns"] += perf_counter_ns()-begin
            selected = cases.parents(graph, analyses, identity)
            records.emit("events", {**identity, "event": "panel", "eligible": len(eligible), "parents": selected})
            for stratum, parent in selected:
                for mi, model in enumerate(PROTOCOL["models"]):
                    for search_seed in PROTOCOL["search_seeds"]:
                        block(instance, params[model], graph.space.state(parent),
                            {**identity, "stratum": stratum, "parent": parent, "model": model, "search_seed": search_seed,
                             "parent_strict": bool(analyses[mi]["strict"][parent])}, records, counts)
                print(f"PANEL {number}/12 {identity} {stratum} parent={parent} runs={counts['search_runs']}", flush=True)
            records.flush()
            counts["instances"] += 1
        assert counts["instances"] == 12 and counts["search_runs"] == 2592 and counts["census_full"] == 442368
        counts["total_new_full_calls"] = sum(counts[k] for k in ("reference_full", "census_full", "sample_QA_full", "search_full", "search_QA_full"))
        save(output/"completion.json", {"status": "complete", "counts": dict(counts), "wall_ns": perf_counter_ns()-started})
    except BaseException:
        save(output/"failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output

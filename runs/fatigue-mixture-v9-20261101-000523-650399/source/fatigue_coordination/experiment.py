"""Frozen full-state census, exact ordinary neighborhoods, and counterfactuals."""
from collections import Counter
from time import perf_counter_ns
import traceback
import numpy as np
from scipy.sparse import csr_matrix
from .protocol import PROTOCOL
from .instances import make_instance, parameters, instance_record
from .space import Space, build_graph
from .analysis import analyze, paired_counts
from .artifacts import create
from .records import Records, save
from .census import evaluate
from .witnesses import make_certificates
from . import panels


def checked_graph(jobs, output, counts):
    started = perf_counter_ns()
    graph = build_graph(Space(jobs))
    assert graph.space.size == PROTOCOL["physical_states"][str(jobs)]
    assert len(graph.destination) == PROTOCOL["labelled_N1_edges"][str(jobs)]
    matrix = csr_matrix((np.ones(len(graph.destination), dtype=bool), (graph.source, graph.destination)),
                        shape=(graph.space.size, graph.space.size))
    assert (matrix != matrix.T).nnz == 0
    np.savez_compressed(output/f"space_N{jobs}.npz", queues=np.array([sum(q, ()) for q in graph.space.queues]),
        split=np.array([len(q[0]) for q in graph.space.queues]), pointer=graph.pointer, destination=graph.destination)
    counts["graph_ns"] += perf_counter_ns()-started
    print(f"GRAPH N={jobs} states={graph.space.size} edges={len(graph.destination)} reversible=TRUE", flush=True)
    return graph


def run_case(jobs, seed, graph, output, records, counts):
    identity = {"jobs": jobs, "seed": seed}
    directory = output/f"N{jobs}-seed{seed}"
    directory.mkdir()
    instance = make_instance(jobs, seed)
    params, metadata = parameters(instance, seed)
    save(directory/"instance.json", instance_record(instance))
    save(directory/"fatigue.json", metadata)
    tables, C, H, reference = evaluate(instance, params, graph.space, directory, records, counts, identity)
    analyses, values = {}, {}
    started = perf_counter_ns()
    for mi, model in enumerate(PROTOCOL["models"]):
        for target, weights in PROTOCOL["targets"].items():
            value = tables[mi] @ (np.asarray(weights)/reference)
            result = analyze(graph, value, PROTOCOL["epsilon"])
            analyses[model, target], values[model, target] = result, value
            np.savez_compressed(directory/(model+"_"+target+"_landscape.npz"), values=value,
                                **{k: v for k, v in result.items() if k != "summary"})
            records.emit("census", {**identity, "model": model, "target": target, **result["summary"]})
            counts["landscapes"] += 1
    counts["landscape_ns"] += perf_counter_ns()-started
    for model in ("strong_fast", "strong_slow"):
        for target in PROTOCOL["targets"]:
            records.emit("paired", {**identity, "dynamic_model": model, "target": target,
                **paired_counts(analyses["beta0", target], analyses[model, target])})
    started = perf_counter_ns()
    make_certificates(instance, params, graph, tables, C, H, reference, analyses, values,
                      records, counts, identity, PROTOCOL["epsilon"])
    counts["witness_QA_ns"] += perf_counter_ns()-started
    panels.run(instance, params, graph, tables, reference, analyses, values, records, counts, identity)
    counts["instances"] += 1
    records.flush()
    print(f"CASE {counts['instances']}/8 N={jobs} seed={seed} witnesses={counts['witnesses']} trials={counts['control_trials']}", flush=True)


def run(project):
    started = perf_counter_ns()
    output, counts = create(project), Counter()
    counts["snapshot_ns"] = perf_counter_ns()-started
    records, active = Records(output), None
    print(f"RUN_DIRECTORY {output}", flush=True)
    try:
        for jobs in PROTOCOL["job_counts"]:
            graph = checked_graph(jobs, output, counts)
            for seed in PROTOCOL["seeds"]:
                active = {"jobs": jobs, "seed": seed}
                run_case(jobs, seed, graph, output, records, counts)
        assert counts["census_full"] == 230400 and counts["instances"] == 8 and counts["landscapes"] == 96
        counts["total_full_calls"] = sum(counts[k] for k in ("reference_full", "census_full", "sample_QA_full",
            "witness_full", "control_parent_full", "control_child_full", "control_final_QA_full"))
        save(output/"completion.json", {"status": "complete", "counts": dict(counts), "wall_ns": perf_counter_ns()-started})
    except BaseException:
        save(output/"failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output

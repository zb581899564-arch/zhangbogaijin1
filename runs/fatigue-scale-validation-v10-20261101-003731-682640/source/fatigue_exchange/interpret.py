"""Posthoc read-only reachability explanation; no new search or decoder calls."""
import os
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
from pathlib import Path
from time import perf_counter_ns
import shutil
import numpy as np
from research.fatigue_coordination.audit import load_graph
from .coverage import n2_endpoints
from .records import read, save


def barrier_limits(output, graph, rows):
    result = []
    for key in sorted({(r["instance_seed"], r["parent"]) for r in rows}):
        seed, parent = key
        local = [r for r in rows if (r["instance_seed"], r["parent"]) == key]
        flags = {r["method"]: r["can_improve"] for r in local}
        missed = not flags["swap_rebind"] and not flags["rebind"]
        if not missed:
            continue
        with np.load(output/f"N4-seed{seed}/physical_tables.npz") as table:
            values = table["objectives"][1, :, 1]/table["reference"][1]
        endpoints = n2_endpoints(graph, parent)
        improved = endpoints[values[endpoints] < values[parent]-1e-10]
        current = len(graph.space.state(parent).queues[0])
        same_counts = [int(i) for i in improved if len(graph.space.state(i).queues[0]) == current]
        result.append({"instance_seed": seed, "parent": parent,
            "improving_N2_endpoints": len(improved), "same_factory_counts_improving_endpoints": len(same_counts),
            "every_N2_improvement_changes_factory_counts": not bool(same_counts)})
    return result


def uniform_bounds(output, graph, events):
    result = []
    counts = np.array([len(graph.space.state(i).queues[0]) for i in range(graph.space.size)])
    for event in events:
        if event.get("event") != "panel" or event["split"] != "confirmation":
            continue
        seed = event["instance_seed"]
        parent = next(int(p) for stratum, p in event["parents"] if stratum == "uniform")
        with np.load(output/f"N4-seed{seed}/physical_tables.npz") as table:
            values = table["objectives"][1, :, 1]
        lower = float(values.min())
        restricted = float(values[counts == counts[parent]].min())
        with np.load(output/f"N4-seed{seed}/strong_fast_TEC_landscape.npz") as landscape:
            barrier_parent = next(int(p) for stratum, p in event["parents"] if stratum.startswith("barrier"))
            actual_strict = bool(landscape["strict"][barrier_parent])
        result.append({"instance_seed": seed, "uniform_parent": parent, "F0_job_count": int(counts[parent]),
            "initial_TEC": float(values[parent]), "global_min_TEC": lower, "fixed_counts_min_TEC": restricted,
            "global_gain_ceiling_pct": float(100*(1-lower/values[parent])),
            "fixed_counts_gain_ceiling_pct": float(100*(1-restricted/values[parent])),
            "barrier_panel_parent": barrier_parent, "barrier_panel_is_strict_under_fast": actual_strict})
    return result


def run(output):
    started = perf_counter_ns()
    graph = load_graph(output, 4)
    rows = [r for r in read(output, "coverage") if r["split"] == "confirmation"
            and r["model"] == "strong_fast" and r["parent_strict"]]
    parents = {(r["instance_seed"], r["parent"]) for r in rows}
    missed = barrier_limits(output, graph, rows)
    core = output/"source/fatigue_mechanism"
    project = output.parents[1]
    sources = list(core.rglob("*.py"))
    assert all(f.read_bytes() == (project/"research/fatigue_mechanism"/f.relative_to(core)).read_bytes() for f in sources)
    result = {"posthoc": True, "new_decoder_calls": 0, "strict_parents": len(parents),
        "missed_by_rebind_and_swap_rebind": missed,
        "uniform_parent_fixed_count_bounds": uniform_bounds(output, graph, list(read(output, "events"))),
        "shared_core_files_still_byte_equal": len(sources), "wall_ns": perf_counter_ns()-started}
    directory = output/"posthoc_source"
    directory.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__), directory/"interpret.py")
    save(output/"interpretation.json", result)
    print({"strict": len(parents), "union_missed": len(missed), "requires_load_count_change": sum(r["every_N2_improvement_changes_factory_counts"] for r in missed)}, flush=True)
    print(result["uniform_parent_fixed_count_bounds"], flush=True)


if __name__ == "__main__":
    import sys
    run(Path(sys.argv[1]))

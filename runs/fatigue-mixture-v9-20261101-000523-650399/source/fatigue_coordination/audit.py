"""Read-back audit using explicit labelled two-step paths and raw outputs."""
from collections import Counter
import json
from time import perf_counter_ns
import numpy as np
from .records import read, save
from .space import Space, Graph


def load_graph(output, jobs):
    with np.load(output/f"space_N{jobs}.npz") as data:
        pointer, destination = data["pointer"], data["destination"]
    groups = np.repeat(np.arange(len(pointer)-1, dtype=np.int32), np.diff(pointer))
    return Graph(Space(jobs), pointer, destination, groups)


def explicit_two(graph, values, parent):
    """Direct set of legal endpoints; independent of the optimized minima routine."""
    best = np.inf
    for first in range(graph.space.jobs):
        for middle in graph.neighbors(parent, first):
            for second in range(graph.space.jobs):
                if first != second:
                    best = min(best, float(values[graph.neighbors(middle, second)].min()))
    return best


def audit(output):
    started = perf_counter_ns()
    protocol = json.loads((output/"protocol.json").read_text(encoding="utf-8"))
    completion = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    counts, census = Counter(), list(read(output/"census.jsonl"))
    assert completion["status"] == "complete" and len(census) == 96
    for jobs in protocol["job_counts"]:
        graph = load_graph(output, jobs)
        for seed in protocol["seeds"]:
            folder = output/f"N{jobs}-seed{seed}"
            with np.load(folder/"physical_tables.npz") as table:
                objectives, reference = table["objectives"], table["reference"]
            assert objectives.shape == (3, graph.space.size, 3)
            sampled = np.random.default_rng(20261128+seed).choice(graph.space.size, 8, replace=False)
            for mi, model in enumerate(protocol["models"]):
                for target, weights in protocol["targets"].items():
                    with np.load(folder/f"{model}_{target}_landscape.npz") as data:
                        values, one, two = data["values"], data["best_one"], data["best_two"]
                        np.testing.assert_array_equal(values, objectives[mi] @ (np.asarray(weights)/reference))
                        for parent in sampled:
                            neighbors = graph.destination[graph.row_pointer[parent]:graph.row_pointer[parent+1]]
                            assert one[parent] == values[neighbors].min()
                            assert two[parent] == explicit_two(graph, values, int(parent))
                            counts["explicit_N1_N2_checks"] += 1
                        local, weak, strict = data["N1_local"], data["weak"], data["strict"]
                        np.testing.assert_array_equal(local, one >= values-protocol["epsilon"])
                        np.testing.assert_array_equal(weak, local & (two < values-protocol["epsilon"]))
                        component = data["component"]
                        np.testing.assert_array_equal(strict, weak & ~data["component_lower_exit"][component]
                                                      & data["component_certified"][component])
                        row = next(r for r in census if (r["jobs"], r["seed"], r["model"], r["target"]) == (jobs, seed, model, target))
                        assert row["weak_N2_states"] == int(weak.sum()) and row["strict_N2_states"] == int(strict.sum())
                    counts["landscapes"] += 1
    controls = list(read(output/"controls.jsonl"))
    for row in controls:
        assert row["full_decodes"] == 17 and len(row["rows"]) == 16
        assert row["best_value"] == min([row["before_value"]]+[c["value"] for c in row["rows"]])
        probability = row["offline_exact_distribution"]
        if probability["one_draw_success"] == 0:
            assert row["gain"] <= protocol["epsilon"]
    assert len(controls) == completion["counts"]["control_trials"]
    assert len(controls)*17 == completion["counts"]["control_parent_full"]+completion["counts"]["control_child_full"]
    counts["controls"] = len(controls)
    for row in read(output/"paired.jsonl"):
        assert sum(row["weak"].values()) == protocol["physical_states"][str(row["jobs"])]
        assert sum(row["strict"].values()) == protocol["physical_states"][str(row["jobs"])]
        counts["paired_rows"] += 1
    counts["witnesses"] = sum(1 for _ in read(output/"witnesses.jsonl"))
    assert counts["witnesses"]*6 == completion["counts"]["witness_full"]
    result = {"status": "pass", "checks": dict(counts), "audit_ns": perf_counter_ns()-started,
              "scope": "all saved classifications/counts and scores; independent explicit N1/N2 paths at8 fixed states per landscape; live full-trace QA separate"}
    save(output/"audit.json", result)
    return result

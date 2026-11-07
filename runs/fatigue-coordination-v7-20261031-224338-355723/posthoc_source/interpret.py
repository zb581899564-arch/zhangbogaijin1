"""Post-census explanation only: no new candidate policy or decoder calls."""
from dataclasses import asdict
from pathlib import Path
import json
import os
import shutil
from time import perf_counter_ns
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
import numpy as np
from .audit import load_graph
from .records import read, save


def improving_pairs(graph, values, parent, epsilon):
    pairs = []
    for first in range(graph.space.jobs):
        for second in range(graph.space.jobs):
            if first == second:
                continue
            if any(np.any(values[graph.neighbors(mid, second)] < values[parent]-epsilon)
                   for mid in graph.neighbors(parent, first)):
                pairs.append((first, second))
    return pairs


def explain(output):
    started = perf_counter_ns()
    corrected = output/"controls.corrected.jsonl"
    controls = list(read(corrected if corrected.exists() else output/"controls.jsonl"))
    graphs = {n: load_graph(output, n) for n in (3, 4)}
    distributions, coverage = [], []
    for row in controls:
        if row["model"] == "beta0" or not row["parent_strict"]:
            continue
        distributions.append({k: row[k] for k in ("jobs", "seed", "model", "parent", "method", "gain", "elapsed_ns", "fallback")}
                             | row["offline_exact_distribution"])
        if row["method"] != "plain_composite":
            continue
        graph, parent = graphs[row["jobs"]], row["parent"]
        with np.load(output/f"N{row['jobs']}-seed{row['seed']}"/f"{row['model']}_TEC_landscape.npz") as data:
            pairs = improving_pairs(graph, data["values"], parent, 1e-10)
        attrs = graph.space.state(parent).genome().by_job()
        cross = [p for p in pairs if attrs[p[0]][0] != attrs[p[1]][0]]
        coverage.append({k: row[k] for k in ("jobs", "seed", "model", "parent")}
                        | {"improving_directed_job_pairs": pairs, "cross_factory_pairs": cross,
                           "all_improving_pairs_cross_factory": len(pairs) == len(cross)})
    example = json.loads((output/"summary.json").read_text(encoding="utf-8"))["example"]
    graph = graphs[example["jobs"]]
    folder = output/f"N{example['jobs']}-seed{example['seed']}"
    parent = example["parent"]
    neighbors = graph.destination[graph.row_pointer[parent]:graph.row_pointer[parent+1]]
    with np.load(folder/"physical_tables.npz") as table:
        objectives, reference = table["objectives"], table["reference"]
        baseline_best = int(neighbors[np.argmin(objectives[0, neighbors, 1])])
        counterfactual = {"state": baseline_best, "genome": asdict(graph.space.state(baseline_best).genome()),
                          "objectives_by_model": objectives[:, baseline_best], "reference": reference}
    result = {"status": "complete", "posthoc": True, "new_decoder_calls": 0,
        "scope": "explain frozen v7 outcomes, no reselected seeds/parents or tuned sampling rules",
        "dynamic_strict_distributions": distributions, "improving_pair_coverage": coverage,
        "example_beta0_best_N1_counterfactual": counterfactual, "wall_ns": perf_counter_ns()-started}
    directory = output/"posthoc_source"
    directory.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__), directory/"interpret.py")
    save(output/"interpretation.json", result)
    print(json.dumps({"panels": len(coverage), "all_improving_pairs_cross_factory": sum(r["all_improving_pairs_cross_factory"] for r in coverage),
                      "counterfactual": counterfactual}, default=lambda x: x.tolist(), ensure_ascii=False), flush=True)
    return result


if __name__ == "__main__":
    import sys
    explain(Path(sys.argv[1]))

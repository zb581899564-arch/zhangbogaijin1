"""Read-only checks and post-hoc descriptions of saved mechanism records.

No decoder, optimizer or parameter search is invoked. Audit output is a new
derived file; frozen protocol, source, predictions and observations stay intact.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys
import numpy as np
from .statistics import selection_metrics


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def key(row):
    return row["instance"], row["parent_seed"], row["profile"]


def audit_run(path):
    protocol = json.loads((path / "protocol.json").read_text(encoding="utf-8"))
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    data = {name: read_rows(path / (name + ".jsonl"))
            for name in ("inputs", "predictions", "candidates", "selections", "timing")}
    n = len(protocol["instances"]) * len(protocol["parent_seeds"]) * len(protocol["profiles"])
    expected = {"inputs": n, "predictions": n, "candidates": 16*n, "selections": 12*n, "timing": n}
    assert {name: len(rows) for name, rows in data.items()} == expected
    pools, parents, candidate_map = {}, {}, defaultdict(list)
    for row in data["inputs"]:
        parent_key = key(row)[:2]
        assert parents.setdefault(parent_key, row["genome"]) == row["genome"]
    for row in data["candidates"]:
        candidate_map[key(row)].append(row)
    for case_key, candidates in candidate_map.items():
        assert [c["index"] for c in candidates] == list(range(16))
        signature = [(c["kind"], c["jobs"], c["genome"]) for c in candidates]
        assert pools.setdefault(case_key[:2], signature) == signature
    selected = {(key(r), r["target"], r["method"]): r for r in data["selections"]}
    same_support, checked, direction_stats = 0, 0, defaultdict(lambda: defaultdict(list))
    for prediction in data["predictions"]:
        candidates = candidate_map[key(prediction)]
        scale = np.asarray(prediction["parent_objectives"])
        for target, weights in protocol["targets"].items():
            actual = np.asarray([c["delta"] for c in candidates]) @ (np.asarray(weights) / scale)
            p = prediction["targets"][target]
            same_support += p["ties"]["fatigue_adjoint"] == p["ties"]["time_only"]
            for method in protocol["methods"]:
                recalculated = selection_metrics(p["scores"].get(method), actual)
                row = selected[key(prediction), target, method]
                for field, value in recalculated.items():
                    if value is None or isinstance(value, list):
                        assert value == row[field]
                    else:
                        np.testing.assert_allclose(value, row[field], atol=1e-12, rtol=1e-12)
                checked += 1
                for field in ("rank_spearman", "sign_accuracy", "accepted_gain", "improvement_probability"):
                    if row[field] is not None:
                        direction_stats[target][method + ":" + field].append(row[field])
    time_stats = defaultdict(list)
    for row in data["timing"]:
        common = row["common"]
        for name, part in common.items():
            assert len(part["samples_ms"]) == 5 and part["warmups"] == 1
            time_stats[name + "_ms"].append(part["median_ms"])
        for target in row["targets"].values():
            for method in ("fatigue_adjoint", "time_only"):
                parts = target["components"][method]
                for name, part in parts.items():
                    assert len(part["samples_ms"]) == 5 and part["warmups"] == 1
                    time_stats[method + "_" + name + "_ms"].append(part["median_ms"])
            for name, value in target["cost_proxy"].items():
                time_stats[name].append(value)
    accounting = summary["full_decode_accounting"]
    assert accounting == {"parent_for_prediction": n, "offline_all_candidate_truth": 16*n,
                          "timing_plain": 6*n, "timing_trace": 6*n}
    stats = {name: {"mean": float(np.mean(values)), "median": float(np.median(values)),
                    "min": float(np.min(values)), "max": float(np.max(values))} for name, values in time_stats.items()}
    candidates = data["candidates"]
    return {"status": "passed", "scope": "post-hoc record audit and descriptive summaries; no new experiment",
            "record_counts": expected, "selection_metrics_recomputed": checked,
            "same_fatigue_vs_control_choice_support": same_support, "choice_comparisons": 4*n,
            "direction_means_across_profiles_descriptive_only": {t: {k: float(np.mean(v)) for k, v in values.items()}
                                                                 for t, values in direction_stats.items()},
            "timing_descriptions": stats,
            "candidates_with_later_topology_change": sum(c["later_topology_changed_ops"] > 0 for c in candidates),
            "mean_later_topology_changed_ops": float(np.mean([c["later_topology_changed_ops"] for c in candidates])),
            "max_direct_defects": max(c["direct_defects"] for c in candidates),
            "parent_negative_start_slopes": sum(c["parent_validation"]["negative_start_slope"] for c in summary["cases"]),
            "candidate_negative_start_slopes": sum(c["validation"]["negative_start_slope"] for c in candidates),
            "full_decode_calls": sum(accounting.values()), "source_of_truth": "saved JSON/JSONL only"}


if __name__ == "__main__":
    output = audit_run(Path(sys.argv[1]))
    destination = Path(sys.argv[1]) / "audit.json"
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(output, ensure_ascii=False, indent=2))

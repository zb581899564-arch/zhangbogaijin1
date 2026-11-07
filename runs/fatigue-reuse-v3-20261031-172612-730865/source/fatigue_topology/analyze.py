"""Analyze a completed frozen run; never redo decodes or overwrite raw data."""
from collections import defaultdict
from pathlib import Path
import json
import sys
import numpy as np
from research.fatigue_mechanism.statistics import selection_metrics
from .experiment import save
from .summary import summarize


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def audit(path, data, completion):
    expected = {"inputs": 90, "predictions": 540, "observations": 5760, "selections": 6480, "timing": 630}
    assert {name: len(rows) for name, rows in data.items()} == expected
    pools, observations, signatures, parents = {}, defaultdict(list), {}, {}
    for row in data["inputs"]:
        k = row["instance"], row["parent_seed"]
        assert parents.setdefault(k, row["genome"]) == row["genome"]
    for row in data["observations"]:
        k = row["instance"], row["parent_seed"], row["profile"], row["pool"]
        observations[k].append(row)
    for k, rows in observations.items():
        signature = [r["trial"] for r in rows]
        common_key = k[0], k[1], k[3]
        assert signatures.setdefault(common_key, signature) == signature
    for row in data["predictions"]:
        k = row["instance"], row["parent_seed"], row["profile"], row["pool"]
        pools[k] = row
    for row in data["selections"]:
        k = row["instance"], row["parent_seed"], row["profile"], row["pool"]
        scores = pools[k]["targets"][row["target"]]["scores"].get(row["method"])
        actual = [r["targets"][row["target"]]["actual"] for r in observations[k]]
        recalculated = selection_metrics(scores, actual)
        for field, value in recalculated.items():
            if value is None or isinstance(value, list):
                assert value == row[field]
            else:
                np.testing.assert_allclose(value, row[field], atol=1e-12, rtol=1e-12)
        for q, cost in row["cost_ms_by_q"].items():
            np.testing.assert_allclose(row["rate_by_q"][q], row["accepted_gain"] / cost)
    assert completion["calls"] == {"parent_prediction": 90, "timing_plain": 540, "timing_trace": 540,
                                    "diagnostic_stage0": 5760, "diagnostic_fixed_later": 5760,
                                    "offline_adaptive_truth": 5760}
    return {"status": "passed", "counts": expected, "recomputed_selections": 6480,
            "same_inputs_and_pools_across_profiles": True, "no_new_decodes": True}


def run(path):
    data = {name: read(path / (name + ".jsonl"))
            for name in ("inputs", "predictions", "observations", "selections", "timing")}
    protocol = json.loads((path / "protocol.json").read_text(encoding="utf-8"))
    completion = json.loads((path / "completion.json").read_text(encoding="utf-8"))
    evidence = audit(path, data, completion)
    save(path / "audit.json", evidence)
    summary = summarize(data["observations"], data["selections"], completion, protocol)
    save(path / "summary.json", summary)
    print(json.dumps({"audit": evidence, "regime_counts": summary["regime_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]))

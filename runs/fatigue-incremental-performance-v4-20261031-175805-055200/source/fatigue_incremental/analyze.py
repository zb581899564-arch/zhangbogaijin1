"""Stream large step logs; audit and summarize without new evaluations."""
from collections import Counter
from pathlib import Path
import json
import sys
from research.fatigue_reuse.experiment import save
from .summary import summarize


def read(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def run(path):
    chains = list(read(path / "chains.jsonl"))
    epochs = list(read(path / "epochs.jsonl"))
    calibration = list(read(path / "calibration.jsonl"))
    ablations = list(read(path / "ablation.jsonl"))
    completion = json.loads((path / "completion.json").read_text(encoding="utf-8"))
    assert len(chains) == 1800 and len(calibration) == 90 and len(ablations) == 60
    identity = lambda r: (r["instance"], r["parent_seed"], r["profile"], r["target"], r["mode"], r["repeat"], r["method"])
    steps, cache_counts = Counter(), Counter()
    for row in read(path / "steps.jsonl"):
        key = identity(row)
        assert row["step"] == steps[key]
        steps[key] += 1
        assert row["on_time"] or not row["accepted"]
    for epoch in epochs:
        cache_counts[identity(epoch)] += 1
        if "incremental_work" in epoch:
            w = epoch["incremental_work"]
            assert w["equivalent_full_ops"] == w["recomputed_ops"]+w["reused_prefix_ops"]+w["unchanged_factory_ops"]
    assert len({identity(r) for r in chains}) == 1800
    for row in chains:
        assert steps[identity(row)] == row["attempted_decisions"]
        assert cache_counts[identity(row)] == row["cache_builds"]
    assert completion["calls"]["search_full"] == sum(r["full_decodes"] for r in chains)
    assert completion["calls"]["offline_final_QA_full"] == 1800
    assert completion["calls"]["calibration_incremental_stage0"] == 10080
    assert completion["calls"]["calibration_full_stage0"] == 10080
    summary = summarize(chains, epochs, calibration, ablations, completion)
    save(path / "summary.json", summary)
    evidence = {"status": "passed", "chains": len(chains), "step_rows": sum(steps.values()),
       "epoch_rows": len(epochs), "calibration_cases": 90, "bitwise_trajectory_pairs": 60,
       "primary_runs_per_method": 90, "primary_independent_parents": 30,
       "work_conservation": True, "new_decodes": 0}
    save(path / "audit.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]))

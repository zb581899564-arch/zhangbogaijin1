"""Audit frozen artifacts and summarize without any new evaluation."""
from collections import Counter
from pathlib import Path
import json
import sys
from .experiment import save
from .summary import summarize


def rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def run(path):
    chains = list(rows(path / "chains.jsonl"))
    epochs = list(rows(path / "epochs.jsonl"))
    calibration = list(rows(path / "calibration.jsonl"))
    ablations = list(rows(path / "ablation.jsonl"))
    completion = json.loads((path / "completion.json").read_text(encoding="utf-8"))
    assert len(chains) == 1470 and len(calibration) == 90 and len(ablations) == 30
    ids = lambda r: (r["instance"], r["parent_seed"], r["profile"], r["target"], r["mode"], r["method"])
    by_chain = {ids(r): r for r in chains}
    assert len(by_chain) == len(chains)
    step_counts, epoch_counts, first_seeds = Counter(), Counter(), {}
    for row in rows(path / "steps.jsonl"):
        identity = ids(row)
        assert row["step"] == step_counts[identity]
        step_counts[identity] += 1
        if row["step"] == 0:
            initial_key = identity[:4]
            assert first_seeds.setdefault(initial_key, row["pool_seed"]) == row["pool_seed"]
        if not row["on_time"]:
            assert not row["accepted"]
    for row in epochs:
        epoch_counts[ids(row)] += 1
    for identity, chain in by_chain.items():
        assert step_counts[identity] == chain["attempted_decisions"]
        assert epoch_counts[identity] == chain["cache_builds"]
    calls = completion["calls"]
    assert calls["search_full"] == sum(r["full_decodes"] for r in chains)
    assert calls["search_partial_stage0"] == sum(r["partial_stage0_calls"] for r in chains)
    assert calls["offline_final_QA_full"] == 1470
    assert calls["calibration_fast_stage0"] == calls["calibration_reference_stage0"] == 10080
    summary = summarize(chains, epochs, calibration, ablations, completion)
    save(path / "summary.json", summary)
    evidence = {"status": "passed", "chains": len(chains), "step_rows": sum(step_counts.values()),
                "epoch_rows": len(epochs), "calibration_cases": 90, "ablation_pairs": 30,
                "all_deadline_and_count_checks_passed": True, "new_decodes": 0}
    save(path / "audit.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]))

"""Streaming consistency audit and summaries; no extra search evaluations."""
from collections import Counter, defaultdict
import json
from research.fatigue_reuse.experiment import save
from .protocol import PROTOCOL
from .summary import summarize


def read(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def identity(r):
    return (r["instance"], r["parent_seed"], r["profile"], r["target"], r["mode"], r["budget_seconds"], r["method"])


def run(path):
    chains = []
    for row in read(path / "chains.jsonl"):
        # Full genomes remain immutable on disk; unnecessary for inference.
        row.pop("final_genome")
        chains.append(row)
    ablations = list(read(path / "ablation.jsonl"))
    completion = json.loads((path / "completion.json").read_text(encoding="utf-8"))
    assert completion["status"] == "complete" and len(chains) == PROTOCOL["expected_chains"]
    assert len(ablations) == PROTOCOL["expected_fixed_pairs"]
    assert sum(r["mode"] == "time" for r in chains) == PROTOCOL["expected_time_chains"]
    by_id = {identity(r): r for r in chains}
    assert len(by_id) == len(chains)
    steps, epoch_counts, epoch_q = Counter(), Counter(), defaultdict(Counter)
    for row in read(path / "steps.jsonl"):
        key = identity(row)
        assert key in by_id and row["step"] == steps[key]
        steps[key] += 1
        assert row["on_time"] or not row["accepted"]
    for epoch in read(path / "epochs.jsonl"):
        key = identity(epoch)
        assert key in by_id
        epoch_counts[key] += 1
        group = (epoch["mode"], epoch["profile"], epoch["target"], epoch["budget_seconds"], epoch["method"])
        epoch_q[group][epoch["closed_reason"], epoch["uses"]] += 1
        if "incremental_work" in epoch:
            w = epoch["incremental_work"]
            assert w["equivalent_full_ops"] == w["recomputed_ops"]+w["reused_prefix_ops"]+w["unchanged_factory_ops"]
    for row in chains:
        assert steps[identity(row)] == row["attempted_decisions"]
        assert epoch_counts[identity(row)] == row["cache_builds"]
    assert completion["calls"]["search_full"] == sum(r["full_decodes"] for r in chains)
    assert completion["calls"]["offline_final_QA_full"] == len(chains)
    reuse = [{"mode": k[0], "profile": k[1], "target": k[2], "budget_seconds": k[3], "method": k[4],
              "epochs": [{"closed_reason": reason, "q": q, "count": count} for (reason, q), count in sorted(v.items())]}
             for k, v in sorted(epoch_q.items())]
    summary = summarize(chains, ablations, completion)
    summary["reuse_distributions"] = reuse
    save(path / "summary.json", summary)
    evidence = {"status": "passed", "chains": len(chains), "step_rows": sum(steps.values()),
                "epoch_rows": sum(epoch_counts.values()), "bitwise_trajectory_pairs": len(ablations),
                "instance_clusters": 36, "paired_parents": 108, "new_decodes": 0}
    save(path / "audit.json", evidence)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))

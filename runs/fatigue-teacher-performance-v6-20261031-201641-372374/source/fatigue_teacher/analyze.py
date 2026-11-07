"""Streaming record audit and immutable summary; no new evaluations."""
from collections import Counter, defaultdict
import json
from .records import read, save
from .summary import summarize
from .protocol import PROTOCOL


def identity(r):
    return (r["instance"], r["parent_seed"], r["regime"], r["block_size"], r["target"], r["mode"], r["method"])


def run(output):
    chains = []
    for row in read(output/"chains.jsonl"):
        for field in ("teacher_bank", "initial_genome", "final_genome"):
            row.pop(field)
        chains.append(row)
    completion = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    config = json.loads((output/"protocol.json").read_text(encoding="utf-8"))
    assert completion["status"] == "complete" and len(chains) == PROTOCOL["expected_total_runs"]
    expected = set()
    for name in config["instances"]:
        for seed in PROTOCOL["parent_seeds"]:
            for regime in PROTOCOL["regimes"]:
                for size in PROTOCOL["block_sizes"]:
                    cells = [(t, "snapshot") for t in PROTOCOL["targets"]]+[("TEC", m) for m in ("steps", "time")]
                    expected.update((name, seed, regime, size, t, mode, method) for t, mode in cells for method in PROTOCOL["methods"])
    by_id = {identity(r): r for r in chains}
    assert set(by_id) == expected and len(by_id) == len(chains)
    steps, epochs, metadata = Counter(), Counter(), defaultdict(Counter)
    for row in read(output/"steps.jsonl"):
        key = identity(row)
        assert key in by_id and row["step"] == steps[key]
        assert row["on_time"] or not row["accepted"]
        steps[key] += 1
        group = (row["mode"], row["target"], row["regime"], row["block_size"], row["method"])
        metadata[group].update({f: int(row["pool_metadata"][f]) for f in ("attempted", "illegal", "unchanged", "duplicates", "unique_candidates", "fallback_noop")})
        metadata[group].update({"decisions": 1, "selected_FA_move": int(row["factory_changes"] > 0)})
    for row in read(output/"epochs.jsonl"):
        epochs[identity(row)] += 1
        if "incremental_work" in row:
            w = row["incremental_work"]
            assert w["equivalent_full_ops"] == w["recomputed_ops"]+w["reused_prefix_ops"]+w["unchanged_factory_ops"]
    for row in chains:
        assert steps[identity(row)] == row["attempted_decisions"]
        assert epochs[identity(row)] == row["cache_builds"]
        assert row["full_decodes"] == 9+row["attempted_decisions"]
        if row["mode"] == "time":
            assert row["deadline_ns"] == 500000000 and row["elapsed_ns"] >= row["deadline_ns"]
        else:
            assert row["full_decodes"] == (10 if row["mode"] == "snapshot" else 33)
    mechanism = list(read(output/"mechanism.jsonl"))
    assert len(mechanism) == PROTOCOL["expected_snapshot_cases"] and all(r["shared_pool_verified"] for r in mechanism)
    assert completion["calls"]["search_full"] == sum(r["full_decodes"] for r in chains)
    assert completion["calls"]["offline_final_full"] == len(chains)
    summary = summarize(chains, mechanism, completion)
    summary["pool_counters"] = [{"mode": k[0], "target": k[1], "regime": k[2], "block_size": k[3], "method": k[4], **dict(v)} for k, v in sorted(metadata.items())]
    save(output/"summary.json", summary)
    evidence = {"status": "passed", "runs": len(chains), "steps": sum(steps.values()), "epochs": sum(epochs.values()),
        "shared_snapshot_pools": len(mechanism), "exact_predeclared_case_set": True,
        "snapshot_full_FE": 10, "fixed24_full_FE": 33, "new_decodes": 0}
    save(output/"audit.json", evidence)
    print(json.dumps(evidence, indent=2))

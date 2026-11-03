"""Post-run independent case/deadline/source audit; no schedule evaluations."""
from pathlib import Path
import json
import sys


def read(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def key(r):
    return (r["instance"], r["parent_seed"], r["regime"], r["block_size"], r["target"], r["mode"], r["method"])


def run(output):
    project = output.parents[1]
    config = json.loads((output/"protocol.json").read_text(encoding="utf-8"))
    expected = set()
    for name in config["instances"]:
        assert (output/name).read_bytes() == (project/"data/chapter4"/name).read_bytes()
        for seed in config["parent_seeds"]:
            for regime in config["regimes"]:
                for size in config["block_sizes"]:
                    cells = [(t, "snapshot") for t in config["targets"]]+[("TEC", m) for m in ("steps", "time")]
                    expected.update((name, seed, regime, size, t, mode, method) for t, mode in cells for method in config["methods"])
    seen, full, bank_full, zero_time = set(), 0, 0, 0
    for row in read(output/"chains.jsonl"):
        identity = key(row)
        assert identity not in seen
        seen.add(identity)
        assert len(row["teacher_bank"]) == 8 and row["teacher_full_decodes"] == 8
        assert row["full_decodes"] == 9+row["attempted_decisions"]
        assert row["gain"] >= -1e-12
        full += row["full_decodes"]
        bank_full += row["teacher_full_decodes"]
        if row["mode"] == "time":
            assert row["deadline_ns"] == int(config["time_budget_seconds"]*1e9)
            assert row["overrun_ns"] == row["elapsed_ns"]-row["deadline_ns"] >= 0
            zero_time += int(row["attempted_decisions"] == 0)
        else:
            assert row["full_decodes"] == (10 if row["mode"] == "snapshot" else 33)
    assert seen == expected and len(seen) == config["expected_total_runs"]
    completion = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    assert completion["calls"]["search_full"] == full and completion["calls"]["teacher_full"] == bank_full
    assert completion["calls"]["offline_final_full"] == len(seen)
    source_count = 0
    for source in (output/"source").rglob("*.py"):
        assert source.read_bytes() == (project/"research"/source.relative_to(output/"source")).read_bytes()
        source_count += 1
    for name in ("chapter4_instance_eligibility.json", "教师结构学习验证协议-v6.md"):
        assert (output/name).read_bytes() == (project/"docs"/name).read_bytes()
    prior = project/"runs/fatigue-expansion-performance-v5-20261031-184248-888305"
    for name in config["instances"]:
        assert json.loads((output/(name+".setup.json")).read_text()) == json.loads((prior/(name+".setup.json")).read_text())
    result = {"status": "passed", "exact_predeclared_cases": len(seen), "all_teacher_full_FE_charged": bank_full,
        "search_full": full, "zero_decision_time_runs_retained": zero_time,
        "frozen_sources_unchanged": source_count, "prior13_SUT_arrays_preserved": True,
        "each_time_deadline_matches_protocol": True, "new_decodes": 0}
    with (output/"design_audit.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]).resolve())

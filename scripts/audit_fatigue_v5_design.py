"""Independent post-run case/deadline/source audit; no new evaluations."""
from pathlib import Path
import json
import sys


def read(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def key(r):
    return (r["instance"], r["parent_seed"], r["profile"], r["target"], r["mode"], r["budget_seconds"], r["method"])


def run(output):
    project = output.parents[1]
    config = json.loads((output / "protocol.json").read_text(encoding="utf-8"))
    schedule = [("strong_fast_recovery", "TEC", b) for b in config["main_budgets_seconds"]]
    schedule += [(p, t, config["secondary_budget_seconds"]) for p, t in config["secondary_cells"]]
    expected = set()
    for name in config["instances"]:
        assert (output / name).read_bytes() == (project / "data/chapter4" / name).read_bytes()
        for seed in config["parent_seeds"]:
            for profile, target, budget in schedule:
                expected.update((name, seed, profile, target, "time", budget, m) for m in config["methods"])
            expected.update((name, seed, "strong_fast_recovery", "TEC", "steps", 0., m) for m in ("cut_time", "cut_time_full"))
    seen, time_rows, fixed_rows = set(), 0, 0
    for row in read(output / "chains.jsonl"):
        identity = key(row)
        assert identity not in seen
        seen.add(identity)
        assert row["gain"] >= -1e-12
        if row["mode"] == "time":
            time_rows += 1
            assert row["deadline_ns"] == int(row["budget_seconds"]*1e9)
            assert row["elapsed_ns"] >= row["deadline_ns"]
            assert row["overrun_ns"] == max(0, row["elapsed_ns"]-row["deadline_ns"])
        else:
            fixed_rows += 1
            assert row["deadline_ns"] is None and row["full_decodes"] == 25
    assert seen == expected and time_rows == 2700 and fixed_rows == 216
    checked_sources = 0
    for source in (output / "source").rglob("*.py"):
        assert source.read_bytes() == (project / "research" / source.relative_to(output / "source")).read_bytes()
        checked_sources += 1
    prior = project / "runs/fatigue-incremental-performance-v4-20261031-175805-055200"
    old_config = json.loads((prior / "protocol.json").read_text(encoding="utf-8"))
    for name in old_config["instances"]:
        assert json.loads((output / (name+".setup.json")).read_text()) == json.loads((prior / (name+".setup.json")).read_text())
    result = {"status": "passed", "exact_predeclared_case_set": len(seen), "time_chains": time_rows,
              "fixed_FE_chains": fixed_rows, "each_deadline_matches_explicit_v5_budget": True,
              "all_frozen_sources_unchanged": checked_sources, "all36_instance_bytes_unchanged": True,
              "prior6_setup_arrays_preserved": True, "new_decodes": 0}
    with (output / "design_audit.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]).resolve())

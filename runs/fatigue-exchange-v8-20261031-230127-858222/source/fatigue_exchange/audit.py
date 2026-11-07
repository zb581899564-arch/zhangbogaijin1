"""Read all budget records; matched snapshot and beta0 negative controls."""
from collections import defaultdict
import json
from time import perf_counter_ns
import numpy as np
from .records import read, save


def block_key(row):
    return tuple(row[k] for k in ("split", "jobs", "instance_seed", "stratum", "parent", "model", "search_seed"))


def check_run(row):
    steps, deadline = row["steps"], row["deadline_ns"]
    assert row["full_decodes"] == 1+len(steps)
    assert row["partial_calls"] == sum(s["partial_calls"] for s in steps)
    assert row["accepted"] == sum(s["accepted"] for s in steps)
    assert row["bookkeeping_ns"] >= 0
    if row["mode"] == "FE":
        assert row["full_decodes"] == 33
    state, value = row["initial_state"], 1.
    for number, step in enumerate(steps):
        assert step["step"] == number and abs(step["before"]-value) < 1e-12
        if step["accepted"]:
            assert step["on_time"] and step["before"]-step["after"] > 1e-10
            assert deadline is None or step["completed_ns"] <= deadline
            state, value = step["child_state"], step["after"]
    assert state == row["final_state"] and abs(row["gain"]-(1-value)) < 1e-12


def audit(output):
    started = perf_counter_ns()
    completion = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    snapshots = {block_key(r): r for r in read(output, "snapshots")}
    runs, full, partial, steps, matched = 0, 0, 0, 0, 0
    beta0, identities = defaultdict(dict), set()
    for row in read(output, "search"):
        check_run(row)
        key = (*block_key(row), row["mode"], row["seconds"], row["method"])
        assert key not in identities
        identities.add(key)
        runs, full, partial, steps = runs+1, full+row["full_decodes"], partial+row["partial_calls"], steps+len(row["steps"])
        if row["mode"] != "FE":
            continue
        if row["method"].startswith("pool_"):
            snap, first = snapshots[block_key(row)], row["steps"][0]
            assert first["chosen"] == snap["methods"][row["method"]]["chosen"]
            np.testing.assert_array_equal(first["objectives"], snap["objectives"][first["chosen"]])
            matched += 1
        if row["model"] == "beta0" and row["method"] in ("pool_time", "pool_fatigue"):
            beta0[block_key(row)][row["method"]] = (row["final_state"], [(s["chosen"], s["child_state"], s["accepted"]) for s in row["steps"]])
    for values in beta0.values():
        assert values["pool_time"] == values["pool_fatigue"]
    counts = completion["counts"]
    assert runs == 5184 == counts["search_runs"] and full == counts["search_full"] and partial == counts["search_partial"]
    assert len(snapshots)*9 == counts["snapshot_full"]
    coverage = 0
    for row in read(output, "coverage"):
        assert 0 <= row["one_draw_success"] <= 1 and 0 <= row["p16"] <= 1
        assert row["improving_N2_coverage"] is None or 0 <= row["improving_N2_coverage"] <= 1
        coverage += 1
    result = {"status": "pass", "search_runs": runs, "steps": steps, "full_calls_checked": full,
        "partial_calls_checked": partial, "same_pool_first_decisions": matched,
        "beta0_exact_FE_trajectory_pairs": len(beta0), "snapshot_blocks": len(snapshots),
        "coverage_rows": coverage, "audit_ns": perf_counter_ns()-started}
    save(output/"audit.json", result)
    return result

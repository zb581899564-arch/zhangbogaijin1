"""Budget, policy replay, exact balancing and coverage identity read-back."""
from collections import Counter, defaultdict
import json
from time import perf_counter_ns
from research.fatigue_exchange.audit import check_run
from .records import read, save
from .policy import family
from .coverage import probabilities


def audit(output):
    started = perf_counter_ns()
    completion = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    counts, keys, branch_controls = Counter(), set(), defaultdict(list)
    for row in read(output, "search"):
        check_run(row)
        key = tuple(row[k] for k in ("split", "instance_seed", "stratum", "model", "search_seed", "mode", "seconds", "method"))
        assert key not in keys
        keys.add(key)
        for step in row["steps"]:
            assert step["family"] == family(row["method"], step["step"], row["streams"]["branch"])
            assert step["proposal_seed"] == row["streams"]["proposal"]+1000003*step["step"]
        if row["mode"] == "FE":
            labels = [s["family"] for s in row["steps"]]
            if row["method"] == "mix_alternate":
                assert Counter(labels) == {"plain": 16, "swap_rebind": 16}
                counts["balanced_FE_runs"] += 1
            control_key = tuple(row[k] for k in ("instance_seed", "stratum", "search_seed", "method"))
            branch_controls[control_key].append(labels)
        counts["search_runs"] += 1
        counts["steps"] += len(row["steps"])
        counts["search_full"] += row["full_decodes"]
    for labels in branch_controls.values():
        assert len(labels) == 3 and labels[0] == labels[1] == labels[2]
    for row in read(output, "coverage"):
        for draws in (16, 32):
            expected = probabilities(row["p_plain"], row["p_swap"], row["method"], draws)
            assert row[f"p{draws}"] == expected
        if row["method"] != "swap_rebind" and row["parent_strict"]:
            assert row["can_improve"] and row["improving_N2_coverage"] == 1.
        counts["coverage_rows"] += 1
    assert counts["search_runs"] == 2592 == completion["counts"]["search_runs"]
    assert counts["search_full"] == completion["counts"]["search_full"]
    counts["cross_model_branch_sequences"] = len(branch_controls)
    result = {"status": "pass", **dict(counts), "audit_ns": perf_counter_ns()-started}
    save(output/"audit.json", result)
    return result

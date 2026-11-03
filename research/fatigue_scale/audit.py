"""All budgets/cells checked, accepted descriptors replayed to final states."""
from collections import Counter
from time import perf_counter_ns
import json
import numpy as np
from research.fatigue_mixture.policy import family
from .cases import instances, cells
from .protocol import PROTOCOL
from .records import read, save
from .state import State, replay


def check(row):
    state = State.from_record(row["initial_state"])
    effective = np.asarray(row["weights"])/row["initial_objectives"]
    value = float(np.asarray(row["initial_objectives"]) @ effective)
    accepted = 0
    for number, step in enumerate(row["steps"]):
        assert step["step"] == number and abs(step["before"]-value) < 1e-12
        assert step["family"] == family(row["method"], number, row["streams"]["branch"])
        assert abs(step["after"]-float(np.asarray(step["objectives"]) @ effective)) < 1e-12
        if step["accepted"] or number % 127 == 0:
            child = replay(state, step["edit"])
            assert step["noop"] == (child == state)
            assert step["load_counts_changed"] == (child.counts() != state.counts())
        if step["accepted"]:
            assert step["on_time"] and step["before"]-step["after"] > 1e-10
            assert row["deadline_ns"] is None or step["completed_ns"] <= row["deadline_ns"]
            state, value, accepted = child, step["after"], accepted+1
    assert state == State.from_record(row["final_state"]) and abs(row["gain"]-(1-value)) < 1e-12
    assert row["accepted"] == accepted and row["full_decodes"] == 1+len(row["steps"])
    assert row["partial_calls"] == 0 and row["bookkeeping_ns"] >= 0
    if row["mode"] == "FE":
        assert row["full_decodes"] == 65
        if row["method"] == "mix_alternate":
            assert Counter(s["family"] for s in row["steps"]) == {"plain":32,"swap_rebind":32}


def audit(project, output):
    started, keys, counts = perf_counter_ns(), set(), Counter()
    for row in read(output, "search"):
        check(row)
        key = tuple(row[k] for k in ("instance","parent_seed","model","target","mode","seconds","method"))
        assert key not in keys
        keys.add(key)
        counts["search_runs"] += 1
        counts["steps"] += len(row["steps"])
        counts["search_full"] += row["full_decodes"]
        counts["noop_children"] += sum(s["noop"] for s in row["steps"])
        counts["late_children"] += sum(not s["on_time"] for s in row["steps"])
    expected = {(name,seed,m,t,mode,seconds,method) for name in instances(project)
                for seed in PROTOCOL["parent_seeds"] for m,t,mode,seconds,_ in cells() for method in PROTOCOL["methods"]}
    assert keys == expected
    completion = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    assert counts["search_full"] == completion["counts"]["search_full"]
    result = {"status":"pass", "counts":dict(counts), "audit_ns":perf_counter_ns()-started,
              "scope":"all cells, budgets, normalized values and branch choices; all accepted edits plus every127th rejected edit replayed"}
    save(output/"audit.json",result)
    return result

"""Configuration and schedule fixed before observing v5 outcomes."""
from copy import deepcopy
from research.fatigue_incremental.protocol import PROTOCOL as V4


PROTOCOL = deepcopy(V4)
PROTOCOL.update({
    "version": "fatigue-expansion-v5",
    "instances": "all 36 eligible instances in frozen eligibility manifest",
    "parent_seeds": [1009, 2027, 4057],
    "pool_seed_base": 20261110,
    "choice_seed_base": 20261111,
    "methods": ["cut_time", "cut_time_full", "local_time", "cut_fatigue", "random"],
    "main_budgets_seconds": [.5, 2.],
    "primary_cell": {"profile": "strong_fast_recovery", "target": "TEC", "budgets": [.5, 2.],
                     "left": "cut_time", "controls": ["cut_time_full", "local_time", "cut_fatigue", "random"]},
    "secondary_cells": [["weak", "TEC"], ["strong_slow_recovery", "TEC"],
                        ["strong_fast_recovery", "balanced"]],
    "secondary_budget_seconds": .5,
    "primary_time_repeats": 1,
    "repeat_statistics": "one timing run per method/case/budget; 108 paired parents in 36 independent instance clusters, not 108 independent instances",
    "validation": {"seeds": [23, 53, 97], "parents_per_case": 3, "candidates_per_parent": 16,
                   "expected_comparisons": 15552, "expected_parent_schedules": 972},
    "fixed_control": "24 decisions, cut_time versus cut_time_full, all 108 strong-fast TEC new-seed parents; bitwise score/choice/accept/final equality required before time trials for that parent",
    "expected_chains": 2916,
    "expected_time_chains": 2700,
    "expected_fixed_pairs": 108,
    "statistics": {"bootstrap_samples": 10000, "sign_flip_samples": 100000, "seed": 20261112,
                   "primary_family": "8 directional contrasts: 2 budgets x 4 controls; one-sided instance-mean paired sign-flip p values with Holm adjustment across all8",
                   "intervals": "hierarchical instance->seed paired bootstrap95, unadjusted effect intervals; instance wins/ties/losses with tolerance1e-10",
                   "strata": "N=20/50/100/150/200 and prior6 versus new30 instances, descriptive, no threshold/seed/budget selection",
                   "secondary": "all positive and negative cells reported; exploratory, no adjusted superiority assertion"},
    "data_mapping": "original6 keep v1-v4 setup/profile seed indices; remaining30 append in sorted manifest order; preserve old data, no cherry-picked new SUT",
    "calibration": "none: unchanged kernels already timed in v4; expanded numerical gate and all108 full/incremental fixed controls retained",
    "ablation": "cut_time_full is FULL first-stage scoring with the same downstream time boundary; every selector still fully decodes selected children",
    "preservation": "new validation then performance directories, protocol and all five packages frozen; no Java/full algorithm changes",
    "no_tuning": True,
})


def instances(project):
    import json
    eligible = json.loads((project / "docs/chapter4_instance_eligibility.json").read_text(encoding="utf-8"))["eligible"]
    original = V4["instances"]
    assert len(eligible) == 36 and set(original) <= set(eligible)
    return list(original) + sorted(set(eligible) - set(original))


def cells():
    main = [("strong_fast_recovery", "TEC", b, True) for b in PROTOCOL["main_budgets_seconds"]]
    return main + [(p, t, PROTOCOL["secondary_budget_seconds"], False) for p, t in PROTOCOL["secondary_cells"]]


def chain_protocol(budget):
    value = deepcopy(PROTOCOL)
    value["time_budget_seconds"] = budget
    return value

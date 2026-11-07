"""V4: exact incremental implementation and measured equal-time comparisons."""
from copy import deepcopy
from research.fatigue_reuse.protocol import PROTOCOL as V3

PROTOCOL = deepcopy(V3)
PROTOCOL.update({
    "version": "fatigue-incremental-v4",
    "parent_seeds": [23, 53, 97, 193, 389],
    "pool_seed_base": 20261106,
    "choice_seed_base": 20261107,
    "incremental": "same-factory tokens (job,machine,worker); reuse exact identical prefix and all unaffected factories; recompute every changed-factory suffix op; no convergence approximation",
    "cache_cost": "build checkpoint lists from paid parent trace, no extra parent decode; include build, all candidate validation/copies/scans/sums and projections in online wall clock",
    "numerical_contract": "C/v and direct-cost addition order exactly match v3 full stage0; fixed-budget score/choice/accept trajectories must match full references",
    "validation": {"seeds": deepcopy(V3["parent_seeds"]), "parents_per_case": 6,
                   "candidates_per_parent": 16, "scope": "90 old-seed scenarios, deterministic legal walks; do before performance, no outcome tuning"},
    "primary_time_repeats": 3,
    "repeat_statistics": "same RNG per initial parent; average timing repeats within parent before 6-instance/5-seed paired bootstrap, never count 90 repeats as independent parents",
    "ablation": "cut_fatigue_full and cut_time_full on all30 strong-fast TEC parents, fixed24 and primary time repeat0; only implementation differs",
    "expected_chains": 1800,
    "main_primary_runs": 90,
    "preservation": "new validation artifact then new performance artifact; old results and Java untouched",
})

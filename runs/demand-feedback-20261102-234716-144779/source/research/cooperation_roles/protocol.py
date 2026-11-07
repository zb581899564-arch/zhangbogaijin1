"""Predeclared six-instance, five-new-seed specialization factorial."""
import copy
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "runs/semantic-repair-20261102-130342-703425"
PLAN = ROOT / "docs/四子群互补来源与专业分工三步验证计划-2026-11-02.md"
SEEDS = [8110301, 8110319, 8110341, 8110367, 8110393]
PHYSICAL_ROLES = ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")
VARIANTS = {
    "SYNC_SPECIAL": {"mode": "SYNC_JOB_ALIGNED", "profile": "SO"},
    "SYNC_UNIFORM": {"mode": "SYNC_JOB_ALIGNED_UNIFORM", "profile": "SO"},
    "SHARE_SPECIAL": {"mode": "SHARE_JOB_ALIGNED", "profile": "SO"},
    "SHARE_UNIFORM": {"mode": "SHARE_JOB_ALIGNED_UNIFORM", "profile": "SO"},
    "NSGA": {"mode": "NSGA2_4V", "profile": "V2"},
}
PAIRS = (("SHARE_SPECIAL", "SHARE_UNIFORM"), ("SYNC_SPECIAL", "SYNC_UNIFORM"),
         ("SHARE_SPECIAL", "SYNC_SPECIAL"), ("SHARE_UNIFORM", "SYNC_UNIFORM")) + tuple(
             (label, "NSGA") for label in VARIANTS if label != "NSGA")


def make_protocol(previous):
    instances = copy.deepcopy(previous["instances"])
    if len(instances) != 6 or [row["time_seconds"] for row in instances] != [3, 4, 5, 9, 12, 19]:
        raise ValueError("Authorized six instances and T budgets changed")
    return {"version": "cooperation-roles-v1", "instances": instances,
        "algorithm_seeds": list(SEEDS), "model": copy.deepcopy(previous["model"]),
        "variants": copy.deepcopy(VARIANTS), "runs": 150, "wall_cap_seconds": 2700,
        "planned_search_seconds": sum(row["time_seconds"] for row in instances) * 25,
        "one_jvm_at_a_time": True, "classic_setting": 0, "method_order_seed": 202611026,
        "time_fractions": [.5, 1.], "fe_checkpoints": [15000],
        "intervention": "SPECIAL versus all-CENTER preference, crossed with shared pool/composition on/off",
        "unchanged": "JOB_ALIGNED;SO;100 particles;four physical groups15/55/15/15;independent Q tables50 steps;original M,C,E,W order;4 FA families x5;80 free;pool8;original cycles;local neighborhoods;G/L;quotas;generation-end guide refresh",
        "observation": "Feedback/composition provenance plus first8+last8 retained-pool requests and full counters; all capture costs inside T; no additional FE/RNG",
        "producer": "Physical source group; retained paid occurrence, not unique inventor or preferred local objective",
        "metrics": {"primary_reference": [1.5]*3, "sensitivity_references": [[1.25]*3, [2.]*3],
            "igdplus_reference": "Each instance all5 methods x all5 seeds deadline-valid T ND union; approximate offline only",
            "aggregation": "Five paired seed HV means per instance, then six instances equally",
            "practical_win": ">=1% instance effect and>=3/5 positive paired seeds; symmetric losses; not significance"},
        "interaction": "(SHARE_SPECIAL-SYNC_SPECIAL)-(SHARE_UNIFORM-SYNC_UNIFORM); raw seed HV differences; instance mean normalized by instance mean SYNC_UNIFORM",
        "specialization_signal": {"meanTPercentAtLeast": 1., "practicalInstanceWinsAtLeast": 3,
            "meanFEPositive": True, "meanTInteractionPositive": True},
        "knowledge_gate": {"variant": "SHARE_SPECIAL", "normalRequestsAtLeast": 10,
            "tightRequestsAtLeast": 3, "missingFactoryPerTightAtLeast": .2,
            "complementaritySnapshotsAtLeast": 1, "distinctChosenPaidFEAtLeast": 2,
            "weightedRelativeGainAtLeast": .001, "seedsPerInstanceAtLeast": 3, "instancesAtLeast": 3,
            "wholeBaseline": "Best score among all retained records' paid wholeObjectives with wholeC<=same cap; missing baseline cannot pass",
            "sourceWithdrawal": "Retained producer labels only; no whole-group causal interpretation"},
        "continuation": "All150 required before quality interpretation; stop on correctness/resources/original45min cap; never rerun an incomplete owner; step3 decision only, no automatic optimizer",
        "cost_boundary": "Original45min includes freeze/start/search/QA/export/main analysis; T contains all search/observation; nested counters not summed as disjoint costs",
        "scope": "Development-factor and knowledge-gap evidence; original36 instances remain development; no formal step6 or publication verdict"}


def validate_protocol(protocol):
    if protocol["algorithm_seeds"] != SEEDS or protocol["variants"] != VARIANTS:
        raise ValueError("Frozen seed/method factors changed")
    if protocol["runs"] != 150 or protocol["wall_cap_seconds"] != 2700:
        raise ValueError("Authorized matrix/cap changed")
    if len(protocol["instances"]) != 6 or len({row["stem"] for row in protocol["instances"]}) != 6:
        raise ValueError("Six unique development instances required")


def jobs(protocol):
    validate_protocol(protocol)
    rng = random.Random(protocol["method_order_seed"])
    result = []
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            labels = list(protocol["variants"]); rng.shuffle(labels)
            result.extend({"phase": "roles", "instance": instance["stem"], "seed": seed,
                "variant": label, "seconds": instance["time_seconds"]} for label in labels)
    if len(result) != 150:
        raise ValueError("Complete6x5x5 matrix required")
    return result


def trial_folder(root, job):
    return root / "trials" / job["phase"] / job["instance"] / str(job["seed"]) / job["variant"]

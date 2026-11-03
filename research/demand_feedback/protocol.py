"""Ninety new-seed runs; no changes to the predeclared feedback rule."""
import copy
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "runs/cooperation-roles-20261102-231315-641007"
PLAN = ROOT / "docs/四子群互补来源与专业分工三步验证计划-2026-11-02.md"
SEEDS = [8110503, 8110521, 8110547, 8110579, 8110601]
VARIANTS = {
    "SHARE_SPECIAL": {"mode": "SHARE_JOB_ALIGNED", "profile": "SO"},
    "SHARE_DEMAND_SPECIAL": {"mode": "SHARE_JOB_ALIGNED_DEMAND", "profile": "SO"},
    "SHARE_SHAM_SPECIAL": {"mode": "SHARE_JOB_ALIGNED_SHAM", "profile": "SO"},
}
PAIRS = (("SHARE_DEMAND_SPECIAL", "SHARE_SHAM_SPECIAL"),
         ("SHARE_DEMAND_SPECIAL", "SHARE_SPECIAL"), ("SHARE_SHAM_SPECIAL", "SHARE_SPECIAL"))


def make_protocol(previous):
    instances = copy.deepcopy(previous["instances"])
    if len(instances) != 6 or [row["time_seconds"] for row in instances] != [3, 4, 5, 9, 12, 19]:
        raise ValueError("Authorized six instances/T budgets changed")
    return {"version": "demand-feedback-v1", "instances": instances,
        "algorithm_seeds": list(SEEDS), "model": copy.deepcopy(previous["model"]),
        "variants": copy.deepcopy(VARIANTS), "runs": 90, "wall_cap_seconds": 1800,
        "planned_search_seconds": sum(row["time_seconds"] for row in instances) * 15,
        "one_jvm_at_a_time": True, "classic_setting": 0, "method_order_seed": 202611027,
        "time_fractions": [.5, 1.], "fe_checkpoints": [15000],
        "precondition": "Step2 complete150 and ELIGIBLE_FIXED_DEMAND_VALIDATION; no instance selection",
        "intervention": "DEMAND and SHAM maintain/query latest per-family tight cap; only DEMAND may replace MAKESPAN family particle's original random intra-VNS factory with largest current relative gap",
        "randomness": "Always retain original random factory draw before demand query; no new RNG or Q layer",
        "unchanged": "Entire SPECIAL/JOB_ALIGNED/SO search, physical groups15/55/15/15, Q50, neighborhoods/acceptance, pool8, cycles/quotas, FA and original execution/refresh timing",
        "metrics": {"primary_reference": [1.5]*3, "sensitivity_references": [[1.25]*3, [2.]*3],
            "igdplus_reference": "Each instance all3 methods x all5 seeds deadline-valid T ND union; approximate offline only",
            "aggregation": "Five paired seed HV means per instance then six instances equally",
            "practical_win": ">=1% instance mean and>=3/5 positive paired seed differences; symmetric losses; not significance"},
        "feedback_signal": {"DEMANDvsSHAMMeanTAtLeast1Percent": True, "DEMANDvsSHAMPracticalWinsAtLeast": 3,
            "DEMANDvsSHAMMeanFEPositive": True, "DEMANDvsOriginalMeanTNonnegative": True,
            "DEMANDvsOriginalMedianTNonnegative": True},
        "continuation": "All90 required before quality interpretation; preserve failures/incomplete owners; no automatic retries, new cap/frequency/rule, or further mechanisms",
        "cost_boundary": "Original30min includes freeze/start/search/QA/export/main analysis; T includes demand maintenance/query and all common observation; extra controller demand validation separately recorded and added once",
        "scope": "One fixed development-period demand-feedback test; no old NSGA wall-clock scores or formal step6"}


def validate_protocol(protocol):
    if protocol["variants"] != VARIANTS or protocol["algorithm_seeds"] != SEEDS:
        raise ValueError("Frozen feedback methods/seeds changed")
    if protocol["runs"] != 90 or protocol["wall_cap_seconds"] != 1800 or len(protocol["instances"]) != 6:
        raise ValueError("Authorized90/original30min contract changed")


def jobs(protocol):
    validate_protocol(protocol); rng = random.Random(protocol["method_order_seed"]); result = []
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            labels = list(protocol["variants"]); rng.shuffle(labels)
            result.extend({"phase": "demand", "instance": instance["stem"], "seed": seed,
                "variant": label, "seconds": instance["time_seconds"]} for label in labels)
    if len(result) != 90 or len({(r["instance"], r["seed"], r["variant"]) for r in result}) != 90:
        raise ValueError("Complete unique6x5x3 matrix required")
    return result


def trial_folder(root, job):
    return root / "trials" / job["phase"] / job["instance"] / str(job["seed"]) / job["variant"]

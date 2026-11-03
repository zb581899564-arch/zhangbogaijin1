"""Minimal synthetic metric, budget, loader and ordering checks; no search/Decoder."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time

from research.dynamic_benchmark.metrics import check_metrics
from research.expansion_screen._metrics import compare
from research.semantic_repair.evidence import read, write_once
from .clock import Deadline
from .execution import command
from .protocol import CLASSICS, ROOT, jobs, make_protocol
from .trials import load_trial
from .checkpoint_checks import write_fixture, run_checkpoint_checks


def synthetic_protocol():
    variants = {"SYNTHETIC_CANDIDATE": {"mode": "UNRUN_SYNTHETIC", "profile": "SO", "setting": 0},
        "SHARE_BASE": {"mode": "SHARE_JOB_ALIGNED", "profile": "SO", "setting": 0},
        "SYNTHETIC_CONTROL": {"mode": "UNRUN_CONTROL", "profile": "SO", "setting": 0}}
    variants.update({label: {"mode": label, "profile": "V2", "setting": setting} for label, setting in CLASSICS.items()})
    for spec in variants.values():
        spec["extra_args"] = ["SNAPSHOT_GENOMES"]
    return make_protocol({"hypothesis": "H1", "candidate": "SYNTHETIC_CANDIDATE", "baseline": "SHARE_BASE",
        "matched_control": "SYNTHETIC_CONTROL", "strong_control": "SYNTHETIC_CONTROL", "variants": variants,
        "algorithm_seeds": [991101, 991103, 991107, 991109, 991113], "method_order_seed": 123,
        "absolute_stop_epoch": time.time() + 100, "mechanism": {"scope": "Synthetic check only; never executed"}})


def _json_lines(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _reject(callback):
    try:
        callback()
    except (ValueError, TimeoutError):
        return
    raise AssertionError("Invalid synthetic evidence was accepted")


def check_loader(folder):
    spec = {"mode": "SPEA2_4V", "profile": "V2", "setting": 1}
    instance = {"stem": "1_1_1_1", "time_seconds": 2, "normalization": {"lower": [0] * 3, "scale": [1] * 3}}
    audit = {"poolCapturePolicy": "first2+last", "paidEvaluationsObserved": 5, "paidArchiveAdmissions": 1,
        "globalSampledPaid": 0, "globalSampledDifferent": 0, "poolsObserved": 0, "poolsCaptured": 0, "auditSeconds": 0.}
    summary = {"status": "passed", "model": "dynamic-append-v1", "mode": "SPEA2_4V", "semanticProfile": "V2",
        "seed": 7, "classicSetting": 1, "incremental": True, "diagnosticSmallSearchConfig": False,
        "checkpointPolicy": "SCREEN-dual", "stopReason": "TIME_LIMIT", "timeLimitSeconds": 2,
        "attempted": 5, "successful": 5, "failed": 0, "timeInterruptedAttempts": 0,
        "archiveSize": 1, "offlineValidationDecodes": 1, "semanticAudit": audit}
    rows = [{"checkpointKind": "TIME", "checkpoint": point, "elapsedSeconds": point, "fe": 5,
        "front": [[.2, .3, .4]], "reached": True, "censored": False} for point in (1., 2.)]
    rows += [{"checkpointKind": "FE", "checkpoint": 15000, "elapsedSeconds": 2., "fe": 5,
        "front": [], "reached": False, "censored": True}]
    write_fixture(folder, rows, summary)
    write_once(folder / "summary.json", summary)
    _json_lines(folder / "anytime.jsonl", rows)
    _json_lines(folder / "semantic-trace.jsonl", [{"type": "audit-summary", **audit}])
    _json_lines(folder / "solutions.jsonl", [{"objectives": [.2, .3, .4], "JS": [1], "FA": [1], "MA": [1], "WA": [1]}])
    run = load_trial(folder, instance, 7, "SPEA2_4V", spec)
    assert run["fe"] is None and run["summary"]["classicSetting"] == 1
    _reject(lambda: load_trial(folder, instance, 7, "SPEA2_4V", {**spec, "setting": 0}))
    summary["attempted"] = summary["successful"] = audit["paidEvaluationsObserved"] = 15000
    (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    _json_lines(folder / "semantic-trace.jsonl", [{"type": "audit-summary", **audit}])
    rows[2].update({"fe": 15000, "elapsedSeconds": 2.001})
    _json_lines(folder / "anytime.jsonl", rows)
    assert load_trial(folder, instance, 7, "SPEA2_4V", spec)["fe"] is None
    rows[0]["elapsedSeconds"] = 1.01
    _json_lines(folder / "anytime.jsonl", rows)
    _reject(lambda: load_trial(folder, instance, 7, "SPEA2_4V", spec))
    return {"setting1AcceptedAs1": True, "settingMismatchRejected": True,
        "unreachedFECensored": True, "postDeadlineFEStaysCensored": True, "futureHalfTimeArchiveRejected": True}


def check_order_and_command(folder):
    protocol = synthetic_protocol()
    order = jobs(protocol)
    assert len(order) == 210 and order == jobs(protocol)
    assert set(row["variant"] for row in order[:7]) == set(protocol["variants"])
    (folder / "classpath.txt").write_text("synthetic-never-executed", encoding="utf-8")
    job = next(row for row in order if row["variant"] == "SPEA2_4V")
    cmd = command(folder, folder / "never-created", job, protocol["variants"]["SPEA2_4V"])
    args = cmd[cmd.index("research.dynamic.DynamicRun") + 1:]
    assert len(args) == 22 and args[14] == "1" and args[15] == "V2" and args[16] == "true"
    assert args[17:21] == ["false"] * 4
    assert args[21] == "SNAPSHOT_GENOMES"
    wrong = deepcopy(protocol)
    wrong["green_all_required"]["versus_BASELINE"]["mean_effect_min_percent"] = 0.
    _reject(lambda: jobs(wrong))
    return {"complete6x5x7": True, "deterministicAllMethodBlockShuffle": True,
        "settingAware22Args": True, "largeObserversDisabled": True, "thresholdReductionRejected": True}


def check_budget(folder):
    started = time.time() - 120
    write_once(folder / "clock.json", {"startedEpoch": started, "wallCapSeconds": 3600, "absoluteStopEpoch": time.time() + 10})
    deadline = Deadline(folder)
    assert deadline.elapsed() >= 120 and 0 < deadline.remaining() <= 10
    _reject(lambda: deadline.require(11))
    return {"resumeKeepsOriginalClock": True, "absoluteStopDominatesCampaignCap": True,
        "insufficientBudgetRejected": True}


def check_censoring():
    seeds = list(range(5))
    index = {(instance, seed, label): {"hv_fe15000": None if instance == "censored" and label == "A" else 1.}
        for instance in ("complete", "censored") for seed in seeds for label in ("A", "B")}
    all_rows = compare(index, "A", "B", ["complete", "censored"], seeds, field="hv_fe15000")
    complete = compare(index, "A", "B", ["complete", "censored"], seeds, field="hv_fe15000", available_only=True)
    assert not all_rows["resolved"] and all_rows["mean_effect_percent"] is None
    assert complete["resolved"] and complete["complete_pair_instances"] == 1
    return {"censoredFullMatrixUnresolved": True, "completePairsReportedSeparately": True}


def check_factorial_and_admission():
    from .metrics import comparisons
    from .gate import admission
    from .interactions import interactions
    protocol = make_protocol(read(ROOT / "research/night_research/h1_context_v1.json"))
    records = []
    levels = {"SHARE_ELITE": 1.03, "SYNC_ELITE": 1.01, "SPEA2_4V": 1.01}
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            for label in protocol["variants"]:
                value = levels.get(label, 1.)
                records.append({"instance": instance["stem"], "seed": seed, "variant": label,
                    "hv": {str(point): value for point in (1.25, 1.5, 2.)}, "hv_half": value,
                    "hv_fe15000": value, "igdplus": .1})
    effects, selected = comparisons(records, protocol)
    assert selected["selected"] == "SPEA2_4V"
    assert admission(protocol, effects, selected)["admitted"]
    factorial = interactions(records, protocol)
    assert abs(factorial["ELITE_refresh_x_sharing"]["T"]["meanInteractionPercent"] - 2.) < 1e-12
    assert factorial["RANDOM_refresh_x_sharing"]["T"]["meanInteractionPercent"] == 0.
    worse_igd = deepcopy(records)
    for row in worse_igd:
        if row["variant"] == "SHARE_ELITE":
            row["igdplus"] = .8
    effects, selected = comparisons(worse_igd, protocol)
    guarded = admission(protocol, effects, selected)
    assert not guarded["admitted"] and "igdplus_guard_BASELINE" in guarded["unmet_green_conditions"]
    return {"globallySelectedSingleClassic": True, "currentV1AllGuardsApplied": True,
        "igdContradictionBlocksAdmission": True, "refreshSharingInteractionRecovered": True}


def run_checks():
    check_metrics()
    from .observation_checks import run_observation_checks
    from .transfer_checks import run_transfer_checks
    from .dimension_checks import run_dimension_checks
    from .report_checks import run_report_check
    with tempfile.TemporaryDirectory(prefix="synthetic-", dir=ROOT / "research/night_research") as temporary:
        folder = Path(temporary)
        result = {"loader": check_loader(folder), "order": check_order_and_command(folder),
            "budget": check_budget(folder), "censoring": check_censoring(),
            "factorialAndAdmission": check_factorial_and_admission(), "contextRenewal": run_observation_checks(),
            "checkpointEvidence": run_checkpoint_checks(folder), "factoryTransfer": run_transfer_checks(),
            "realDimensions": run_dimension_checks(folder), "h2Report": run_report_check(folder)}
    return {"status": "passed", **result, "metricChecks": "exact HV/IGD+/ND", "newSearchFE": 0,
        "newDecodeFE": 0, "optimizerStarted": False}

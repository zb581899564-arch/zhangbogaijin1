"""Validate fixed transfer frequency, full counters and first8+last8 paid events."""
from pathlib import Path
from research.semantic_repair.trials import json_lines
from .validation import integer
from .transfer_records import DIRECTIONS, validate_event

MODES = ("PACKET_ROLE", "MOSAIC_ROLE", "PACKET_RANDOM", "MOSAIC_RANDOM")
SAMPLE_POLICY = "first8+last8 paid transfers; full counters"
MARGINALS = "Three pairs/six draws in every mode; packet uses first selected record for all components"
COUNTERS = ("eligibleOpportunities", "scheduledAttempts", "sourceRandomDraws", "paidTransfers",
    "deadlineValidPaidTransfers", "source0EncodingPreserved", "source0TimelineMatched", "otherFactoriesPreserved", "pendingTransfers")


def require_contract():
    return "factory-transfer-v1"


def validate_counters(counters, summary, mode):
    if counters.get("mode") != mode or counters.get("samplePolicy") != SAMPLE_POLICY:
        raise ValueError("Transfer mode or bounded sample policy changed")
    if counters.get("duplicatesArePaid") is not True or counters.get("sourceMarginals") != MARGINALS:
        raise ValueError("Transfer duplicate charging or common source-draw policy changed")
    for key in COUNTERS:
        integer(counters.get(key), key)
    cells = counters.get("perFamilyDirection")
    expected = {(family, direction) for family in range(4) for direction in DIRECTIONS}
    if not isinstance(cells, list) or len(cells) != 12 or {(cell.get("family"), cell.get("direction")) for cell in cells} != expected:
        raise ValueError("Complete unique four-family x three-boundary-direction opportunity counters required")
    for cell in cells:
        integer(cell.get("family"), "opportunity family", 0, 3)
        integer(cell.get("opportunities"), "opportunities")
    opportunities = sum(cell["opportunities"] for cell in cells)
    attempts = sum(cell["opportunities"] // 4 for cell in cells)
    paid = counters["paidTransfers"]
    if opportunities != counters["eligibleOpportunities"] or attempts != counters["scheduledAttempts"]:
        raise ValueError("Actual per-family/direction fourth-opportunity schedule does not close")
    if counters["sourceRandomDraws"] != 6 * attempts or paid + counters["pendingTransfers"] != attempts:
        raise ValueError("Transfer sampling draws or paid/pending evaluations do not close")
    if paid > summary["successful"] or counters["otherFactoriesPreserved"] != paid:
        raise ValueError("Transfer paid FE or unchanged-other-factories witnesses differ")
    for key in ("deadlineValidPaidTransfers", "source0EncodingPreserved", "source0TimelineMatched"):
        if counters[key] > paid:
            raise ValueError("Transfer witness count exceeds paid transfers: " + key)
    if counters["source0TimelineMatched"] < counters["source0EncodingPreserved"]:
        raise ValueError("Some intact source encodings lack their required timeline witness")
    if mode.startswith("PACKET") and any(counters[key] != paid for key in ("source0EncodingPreserved", "source0TimelineMatched")):
        raise ValueError("PACKET did not preserve every paid source tuple and timeline")


def _sample_counters(checked, counters):
    for key in ("deadlineValid", "source0EncodingPreserved", "source0TimelineMatched"):
        total_key = "deadlineValidPaidTransfers" if key == "deadlineValid" else key
        positives = sum(row[key] for row in checked)
        negatives = len(checked) - positives
        if positives > counters[total_key] or negatives > counters["paidTransfers"] - counters[total_key]:
            raise ValueError("Bounded transfer witnesses contradict complete counters: " + key)
    for previous, current in zip(checked, checked[1:]):
        if (current["paidFE"] <= previous["paidFE"] or current["generation"] < previous["generation"]
                or current["elapsedSeconds"] < previous["elapsedSeconds"]):
            raise ValueError("Paid transfer events ran backwards in FE or generation")


def validate_observation(rows, summary, mode):
    if mode not in MODES:
        raise ValueError("Unknown frozen factory-transfer mode")
    counters = summary.get("cooperation", {}).get("factoryTransfer")
    if not isinstance(counters, dict):
        raise ValueError("Missing summary.cooperation.factoryTransfer")
    validate_counters(counters, summary, mode)
    if not rows or rows[0].get("type") != "factory-transfer-summary":
        raise ValueError("Missing factory-transfer summary header")
    if {key: value for key, value in rows[0].items() if key != "type"} != counters:
        raise ValueError("Transfer header differs from complete summary counters")
    paid = counters["paidTransfers"]
    expected = list(range(1, min(8, paid) + 1)) + list(range(max(9, paid - 7), paid + 1))
    if len(rows) > 17 or [row.get("event") for row in rows[1:]] != expected:
        raise ValueError("Transfer trace escaped first8+last8 paid events")
    checked = [validate_event(row, mode, summary) for row in rows[1:]]
    _sample_counters(checked, counters)
    return {"schema": "factory-transfer-v1", "completeSearchCounters": counters,
        "sampledEvents": checked, "sampledDeadlineValidEvents": sum(row["deadlineValid"] for row in checked),
        "scope": "All paid events, including late ones, contribute counters; only deadline-valid events are cutoff-valid. Local encoding replay is independent; other factories and atomic timelines are Java witnesses."}


def attach(run, spec):
    if spec.get("observation") != {"schema": "factory-transfer-v1"}:
        raise ValueError("Unknown factory-transfer schema")
    modes = {"SHARE_JOB_ALIGNED_" + mode: mode for mode in MODES}
    mode = modes.get(spec["mode"])
    if mode is None:
        raise ValueError("Transfer observation attached to an unregistered mode")
    cooperation = run["summary"].get("cooperation", {})
    if cooperation.get("contextRenewal") is not None or (Path(run["folder"]) / "context-renewal.jsonl").exists():
        raise ValueError("H2 factory transfer cannot combine H1 context renewal")
    rows = json_lines(Path(run["folder"]) / "factory-transfer.jsonl")
    run["mechanismObservation"] = validate_observation(rows, run["summary"], mode)

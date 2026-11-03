"""Setting-aware checkpoint loader; never relabel a setting1 run as setting0."""
import math
from collections import Counter
import numpy as np

from research.semantic_repair.evidence import read
from research.semantic_repair.trials import json_lines, checkpoint, normalized_front
from research.semantic_repair.diagnostics import validate_trace
from .checkpoint_evidence import validate_checkpoint_evidence


def validate_summary(summary, instance, seed, spec):
    expected = {"status": "passed", "model": "dynamic-append-v1", "mode": spec["mode"],
        "semanticProfile": spec["profile"], "seed": seed, "classicSetting": spec["setting"],
        "incremental": True, "diagnosticSmallSearchConfig": False,
        "checkpointPolicy": "SCREEN-dual", "stopReason": "TIME_LIMIT"}
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError("Frozen run identity/budget differs at " + key)
    if abs(summary["timeLimitSeconds"] - instance["time_seconds"]) > 1e-9:
        raise ValueError("Registered T budget changed")
    for key in ("attempted", "successful", "failed", "timeInterruptedAttempts", "archiveSize", "offlineValidationDecodes"):
        if type(summary.get(key)) is not int or summary[key] < 0:
            raise ValueError("Missing or invalid paid-accounting field: " + key)
    if summary["failed"] != summary["timeInterruptedAttempts"]:
        raise ValueError("Genuine evaluation failure must not enter quality analysis")
    if summary["attempted"] != summary["successful"] + summary["failed"]:
        raise ValueError("Broken paid-evaluation accounting")
    if summary["archiveSize"] != summary["offlineValidationDecodes"] or summary["archiveSize"] < 1:
        raise ValueError("Incomplete successful whole returned-archive replay")
    if not isinstance(summary.get("semanticAudit"), dict) or not summary["semanticAudit"].get("enabled", True):
        raise ValueError("Common bounded semantic audit is required")


def load_trial(folder, instance, seed, label, spec):
    summary = read(folder / "summary.json")
    validate_summary(summary, instance, seed, spec)
    rows = json_lines(folder / "anytime.jsonl")
    if len(rows) != 3:
        raise ValueError("Exactly half/T/FE15000 snapshots required")
    seconds = instance["time_seconds"]
    final, half, fe = checkpoint(rows, "TIME", seconds), checkpoint(rows, "TIME", seconds / 2), checkpoint(rows, "FE", 15000)
    if fe.get("reached", True) and fe["fe"] != 15000:
        raise ValueError("FE snapshot contains future successful evaluation")
    # The successful counter may reach15000 just before archive admission
    # crosses T; the recorder correctly censors that checkpoint. The summary
    # counter alone cannot override deadline-valid snapshot evidence.
    lower, scale = (np.asarray(instance["normalization"][key], dtype=float) for key in ("lower", "scale"))
    if lower.shape != (3,) or scale.shape != (3,) or not np.isfinite(lower).all() or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("Invalid frozen normalization")
    solutions = json_lines(folder / "solutions.jsonl")
    if len(solutions) != summary["archiveSize"]:
        raise ValueError("Incomplete returned solution export")
    for solution in solutions:
        if len(solution["objectives"]) != 3 or not all(math.isfinite(x) for x in solution["objectives"]):
            raise ValueError("Malformed returned objectives")
        if any(not isinstance(solution.get(key), list) or not solution[key] for key in ("JS", "FA", "MA", "WA")):
            raise ValueError("Missing returned four-vector encoding")
    trace = json_lines(folder / "semantic-trace.jsonl")
    validate_trace(trace, summary["semanticAudit"], summary)
    if any(row.get("type") == "pool" and row.get("deadlineValid") is True and row["elapsedSeconds"] > seconds + 1e-9 for row in trace):
        raise ValueError("Future semantic pool marked deadline-valid")
    checkpoint_evidence = validate_checkpoint_evidence(folder, rows, summary, instance)
    run = {"instance": instance["stem"], "seed": seed, "variant": label, "summary": summary,
        "final": normalized_front(final, seconds, lower, scale, required=True),
        "half": normalized_front(half, seconds / 2, lower, scale, required=True),
        "fe": normalized_front(fe, seconds, lower, scale), "finalRow": final, "halfRow": half, "feRow": fe,
        "traceSummary": {"rows": len(trace), "types": dict(Counter(row.get("type", "unknown") for row in trace)),
            "deadlineValidPools": sum(row.get("type") == "pool" and row.get("deadlineValid") is True for row in trace),
            "deadlineInvalidPools": sum(row.get("type") == "pool" and row.get("deadlineValid") is not True for row in trace)},
        "checkpointEvidence": checkpoint_evidence, "folder": str(folder),
        "execution": read(folder / "execution.json") if (folder / "execution.json").exists() else None}
    from .observations import attach_observation
    attach_observation(run, spec)
    return run

"""Validate paid checkpoint/semantic evidence before metric construction."""
import json
import math
from collections import Counter
import numpy as np

from .evidence import read
from .diagnostics import validate_trace


def json_lines(path):
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def checkpoint(rows, kind, value):
    matches = [row for row in rows if row["checkpointKind"] == kind
               and abs(row["checkpoint"] - value) < 1e-9]
    if len(matches) != 1:
        raise ValueError("Missing or duplicated checkpoint: " + kind + " " + str(value))
    return matches[0]


def normalized_front(row, deadline, lower, scale, *, required=False):
    reached = row.get("reached", True)
    if not reached:
        if row["front"] or required:
            raise ValueError("Censored required checkpoint or fabricated censored front")
        return None
    if row.get("censored", False) or row["elapsedSeconds"] > deadline + 1e-9:
        raise ValueError("Future or censored archive entered a reached checkpoint")
    points = np.asarray(row["front"], dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points) or not np.isfinite(points).all():
        raise ValueError("Empty, nonfinite or malformed paid archive")
    return (points - lower) / scale


def _validate_summary(summary, instance, seed, spec):
    if summary["status"] != "passed" or summary["failed"] != summary["timeInterruptedAttempts"]:
        raise ValueError("Genuine failure or missing successful offline replay")
    if summary["mode"] != spec["mode"] or summary["semanticProfile"] != spec["profile"]:
        raise ValueError("Semantic profile or algorithm mode differs from the frozen job")
    if summary["seed"] != seed or summary.get("classicSetting") != 0:
        raise ValueError("Seed changed or classical calibration escaped locked setting0")
    if not summary.get("incremental") or summary.get("diagnosticSmallSearchConfig") is not False:
        raise ValueError("Full incremental search configuration was not used")
    if summary.get("checkpointPolicy") != "SCREEN-dual":
        raise ValueError("Wrong snapshot policy")
    if summary["stopReason"] != "TIME_LIMIT" or abs(summary["timeLimitSeconds"] - instance["time_seconds"]) > 1e-9:
        raise ValueError("Wrong registered wall-clock budget")
    if summary["archiveSize"] != summary["offlineValidationDecodes"] or summary["archiveSize"] < 1:
        raise ValueError("Incomplete successful result-archive replay")
    if summary["attempted"] != summary["successful"] + summary["failed"]:
        raise ValueError("Broken paid-evaluation accounting")
    audit = summary.get("semanticAudit")
    if not isinstance(audit, dict):
        raise ValueError("Missing common bounded semantic diagnostics")
    if audit.get("enabled") is False:
        raise ValueError("Common bounded diagnostics were explicitly disabled")


def load_trial(folder, instance, seed, label, spec):
    summary = read(folder / "summary.json")
    _validate_summary(summary, instance, seed, spec)
    rows = json_lines(folder / "anytime.jsonl")
    if len(rows) != 3:
        raise ValueError("Expected exactly half/T/FE15000 checkpoints")
    seconds = instance["time_seconds"]
    final = checkpoint(rows, "TIME", seconds)
    half = checkpoint(rows, "TIME", seconds / 2)
    fe = checkpoint(rows, "FE", 15000)
    if fe.get("reached", True) and fe["fe"] != 15000:
        raise ValueError("Fixed-FE snapshot contains a future successful evaluation")
    lower = np.asarray(instance["normalization"]["lower"], dtype=float)
    scale = np.asarray(instance["normalization"]["scale"], dtype=float)
    if lower.shape != (3,) or scale.shape != (3,) or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("Invalid registered normalization")
    # The Java writer performs complete model replay; verify that its actual
    # export exists and has all of the archived four-vector records as well.
    solutions = json_lines(folder / "solutions.jsonl")
    if len(solutions) != summary["archiveSize"]:
        raise ValueError("Incomplete solution export")
    for solution in solutions:
        if len(solution["objectives"]) != 3 or not all(math.isfinite(x) for x in solution["objectives"]):
            raise ValueError("Malformed exported objectives")
        if any(not solution.get(key) for key in ("JS", "FA", "MA", "WA")):
            raise ValueError("Missing exported four-vector encoding")
    trace = json_lines(folder / "semantic-trace.jsonl")
    validate_trace(trace, summary["semanticAudit"], summary)
    if any(row.get("type") == "pool" and row.get("deadlineValid") is True
           and row["elapsedSeconds"] > seconds + 1e-9 for row in trace):
        raise ValueError("Future pool marked deadline-valid")
    trace_summary = {"rows": len(trace), "types": dict(Counter(row.get("type", "unknown") for row in trace)),
                     "deadlineValidPools": sum(row.get("type") == "pool" and row.get("deadlineValid") is True for row in trace),
                     "deadlineInvalidPools": sum(row.get("type") == "pool" and row.get("deadlineValid") is not True for row in trace)}
    return {"instance": instance["stem"], "seed": seed, "variant": label, "summary": summary,
            "final": normalized_front(final, seconds, lower, scale, required=True),
            "half": normalized_front(half, seconds / 2, lower, scale, required=True),
            "fe": normalized_front(fe, seconds, lower, scale),
            "finalRow": final, "halfRow": half, "feRow": fe,
            "traceSummary": trace_summary, "folder": str(folder),
            "execution": read(folder / "execution.json") if (folder / "execution.json").exists() else None}

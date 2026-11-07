"""Bounded trace shape and paid-evidence checks; no offline optimizer claims."""
import math


def _nonnegative(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _validate_pool(pool):
    candidates = pool["candidates"]
    indices = [row["index"] for row in candidates]
    if len(indices) != len(set(indices)) or not indices:
        raise ValueError("Empty or duplicated candidate index")
    if pool["selector"] not in ("PDDR", "rank-crowding"):
        raise ValueError("Unknown captured selector")
    selected = pool["selectedIndices"]
    if len(selected) != pool["capacity"] or len(selected) != len(set(selected)) or not set(selected).issubset(indices):
        raise ValueError("Malformed captured survivor indices")
    if not _nonnegative(pool["elapsedSeconds"]) or not isinstance(pool["deadlineValid"], bool):
        raise ValueError("Malformed pool deadline evidence")
    for row in candidates:
        if row["source"] not in ("G", "L", "P", "O"):
            raise ValueError("Unknown candidate source")
        if len(row["objectives"]) != 3 or not all(math.isfinite(value) for value in row["objectives"]):
            raise ValueError("Malformed pool objectives")
        if any(not isinstance(row.get(key), list) or not row[key] for key in ("JS", "FA", "MA", "WA")):
            raise ValueError("Pool omitted a replayable four-vector encoding")
    fitness = pool.get("fitness")
    if fitness is not None and (len(fitness) != len(candidates) or not all(math.isfinite(x) for x in fitness)):
        raise ValueError("Malformed full-pool PDDR score array")
    quotas = pool.get("quotas")
    if quotas is not None:
        if quotas != [80, 5, 5, 5, 5]:
            raise ValueError("Cooperation pool quotas changed")
        lookup = {row["index"]: row for row in candidates}
        counts = [sum(lookup[index]["category"] == category for index in selected) for category in range(5)]
        if counts != quotas:
            raise ValueError("Captured cooperation survivors violate registered quotas")


def validate_trace(trace, audit, summary):
    if not trace or trace[0].get("type") != "audit-summary":
        raise ValueError("Missing bounded audit-summary trace row")
    if {key: value for key, value in trace[0].items() if key != "type"} != audit:
        raise ValueError("Trace audit-summary differs from summary.semanticAudit")
    if audit.get("poolCapturePolicy") != "first2+last":
        raise ValueError("Common pool capture policy changed")
    pools = trace[1:]
    if len(pools) > 3 or audit["poolsCaptured"] != len(pools) or any(row.get("type") != "pool" for row in pools):
        raise ValueError("Trace escaped the common three-pool bound")
    for key in ("paidEvaluationsObserved", "paidArchiveAdmissions", "globalSampledPaid", "globalSampledDifferent",
                "poolsObserved", "poolsCaptured", "auditSeconds"):
        if not _nonnegative(audit.get(key)):
            raise ValueError("Missing or nonfinite semantic counter: " + key)
    if audit["paidEvaluationsObserved"] != summary["successful"]:
        raise ValueError("Semantic paid-success callback differs from the guarded evaluator")
    if audit["globalSampledDifferent"] > audit["globalSampledPaid"]:
        raise ValueError("Changed global sample count exceeds paid global samples")
    for pool in pools:
        _validate_pool(pool)

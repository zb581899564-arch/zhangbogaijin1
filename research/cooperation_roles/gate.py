"""Predeclared step3 knowledge gate; missing evidence never passes."""
from .protocol import SEEDS


def seed_decision(instance, seed, counters, snapshots, source):
    required = ("requests", "tightRequests", "tightRequestsMissingFactory")
    available = isinstance(counters, dict) and all(isinstance(counters.get(key), int) for key in required)
    requests = counters.get("requests") if available else None
    tight = counters.get("tightRequests") if available else None
    missing = counters.get("tightRequestsMissingFactory") if available else None
    ratio = missing / tight if available and tight > 0 else None
    complementary = [row["request"] for row in snapshots or [] if row.get("genuineComplementarity") is True]
    conditions = {"normalRequestsAtLeast10": requests is not None and requests >= 10,
        "tightRequestsAtLeast3": tight is not None and tight >= 3,
        "missingFactoryPerTightAtLeast20Percent": ratio is not None and ratio >= .2,
        "genuineComplementaritySnapshotObserved": bool(complementary)}
    return {"instance": instance, "seed": seed, "variant": "SHARE_SPECIAL", "source": source,
        "counterEvidenceAvailable": available, "normalRequests": requests, "tightRequests": tight,
        "tightRequestsMissingFactory": missing, "missingPerTight": ratio,
        "snapshotEvidenceAvailable": snapshots is not None, "capturedSnapshots": len(snapshots) if snapshots is not None else None,
        "genuineComplementarityRequests": complementary, "conditions": conditions,
        "passesAllConditions": available and snapshots is not None and all(conditions.values())}


def knowledge_gate(protocol, runs):
    index = {(run["instance"], run["seed"]): run for run in runs if run["variant"] == "SHARE_SPECIAL"}
    if len(index) != sum(run["variant"] == "SHARE_SPECIAL" for run in runs):
        raise ValueError("Duplicated gate owner")
    decisions, instances = [], []
    for instance in protocol["instances"]:
        stem = instance["stem"]; current = []
        for seed in SEEDS:
            run = index.get((stem, seed))
            counters = run["summary"]["cooperation"].get("poolEvidence") if run else None
            row = seed_decision(stem, seed, counters, run.get("poolReplay") if run else None,
                                run["folder"] + "/cooperation-evidence.jsonl" if run else "MISSING_OWNER")
            decisions.append(row); current.append(row)
        passes = sum(row["passesAllConditions"] for row in current)
        instances.append({"instance": stem, "passingSeeds": passes, "requiredSeeds": 3,
                          "passesInstanceGate": passes >= 3, "seeds": [row["seed"] for row in current if row["passesAllConditions"]]})
    eligible = sum(row["passesInstanceGate"] for row in instances) >= 3
    return {"status": "ELIGIBLE_FIXED_DEMAND_VALIDATION" if eligible else "SKIPPED_NO_IDENTIFIED_ACTIONABLE_GAP",
        "gateSatisfied": eligible, "passingInstances": sum(row["passesInstanceGate"] for row in instances),
        "requiredInstances": 3, "instances": instances, "seedConditions": decisions,
        "step3PerformanceStarted": False, "automaticDispatch": False,
        "baselineRequirement": "A sample must beat parent and best cap-feasible paid whole source by>=0.1%; at least two chosen paidFE",
        "scope": "resource-investment gate; bounded retained pools only; no final HV or whole-group causal attribution",
        "missingEvidence": "Never imputed as zero or used as a passing denominator"}

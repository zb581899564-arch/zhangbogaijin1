"""First-paid-admission role partition, with descriptive three-indicator omissions."""
from collections import Counter

import numpy as np

from run_long_budget_bridge import read, rows, hypervolume, igd_plus, nondominated
from pa_role_flow import ROLES, caller, exposure
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage, objective_set
from research.semantic_repair.evidence import digest


def consume(path, identities):
    identities[str(path)] = digest(path)
    return read(path)


def metrics(front, norm, reference):
    normalized = (front - norm["lower"]) / norm["scale"]
    return {"frontSize": len(front),
        "HV": {str(ref): hypervolume(normalized, (ref,) * 3) for ref in (1.25, 1.5, 2.)},
        "IGDplus": igd_plus(normalized, reference) if len(front) else None,
        "objectiveMin": front.min(axis=0).tolist() if len(front) else None}


def terminal(folder, endpoint, identities):
    path = folder / "checkpoint-solutions.jsonl"
    identities[str(path)] = digest(path)
    selected = [r for r in rows(path) if r["checkpointKind"] == "FE" and r["checkpoint"] == endpoint]
    assert selected and all(1 <= r["bornFE"] <= endpoint == r["checkpointFE"] for r in selected)
    assert len({tuple(r["objectives"]) for r in selected}) == len(selected)
    return selected


def role_partition(records, norm, reference, controls, endpoint):
    jobs = len(records[0]["JS"])
    fees = exposure(endpoint, jobs)
    raw = np.asarray([r["objectives"] for r in records], dtype=float)
    labels = [caller(r["bornFE"], jobs) for r in records]
    whole = metrics(raw, norm, reference)
    group_rows = []
    for role in ("INITIAL", *ROLES):
        chosen = np.asarray([x == role for x in labels], dtype=bool)
        remainder = raw[~chosen]
        without = metrics(remainder, norm, reference)
        comparisons = []
        for name, control in controls.items():
            full_c = bidirectional_coverage(raw, control)
            missing_c = bidirectional_coverage(remainder, control) if len(remainder) else None
            comparisons.append({"control": name, "fullCoverage": full_c, "withoutRoleCoverage": missing_c,
                "fractionOfControlOnlyCoveredByThisFirstCaller": full_c["C_A_B"] - missing_c["C_A_B"] if missing_c else full_c["C_A_B"]})
        den = whole["IGDplus"] + without["IGDplus"] if without["IGDplus"] is not None else None
        group_rows.append({"firstCaller": role, "proposalFE": fees[role], "terminalPoints": int(chosen.sum()),
            "terminalPointFraction": float(chosen.mean()), "withoutRoleMetrics": without,
            "exclusiveHVLossPct": {str(ref): 100 * (1 - without["HV"][str(ref)] / whole["HV"][str(ref)])
                                    for ref in (1.25, 1.5, 2.)},
            "IGDplusSymmetricWorseningOnOmission": 200 * (without["IGDplus"] - whole["IGDplus"]) / den if den else 0. if den == 0 else None,
            "coverageComparisons": comparisons,
            "isAlgorithmAblation": False})
    return {"wholeFront": whole, "groups": group_rows,
        "firstBirthFErange": [min(r["bornFE"] for r in records), max(r["bornFE"] for r in records)],
        "endpointExposure": fees, "retrospectiveDeletionNotCausalAblation": True}


def audit_source(source, phase, identities):
    plan = consume(source / "protocol.json", identities)
    frozen = consume(source / (phase.lower() + "-analysis.json"), identities)
    assert consume(source / "status.json", identities)["status"] == "COMPLETE"
    endpoint = plan["fe100k"] if phase == "FE100K" else plan["fe500k"]
    results = []
    for spec, previous in zip(plan["instances"], frozen["instances"]):
        stem, norm = spec["stem"], spec["normalization"]
        assert stem == previous["stem"]
        records = {(seed, arm): terminal(source / stem / str(seed) / (phase + "-" + arm), endpoint, identities)
                   for seed in plan["seeds"] for arm in plan["arms"]}
        fronts = {key: objective_set([r["objectives"] for r in value]) for key, value in records.items()}
        reference = nondominated(np.vstack([(front - norm["lower"]) / norm["scale"] for front in fronts.values()]))
        old = {(r["seed"], r["arm"]): r for r in previous["observations"]}
        for seed in plan["seeds"]:
            controls = {arm: fronts[seed, arm] for arm in plan["arms"] if not arm.startswith("PA_")}
            for arm in ("PA_JOINT", "PA_RELABEL"):
                row = role_partition(records[seed, arm], norm, reference, controls, endpoint)
                assert np.isclose(row["wholeFront"]["HV"]["1.5"], old[seed, arm]["HV"]["1.5"], rtol=1e-12, atol=1e-12)
                assert np.isclose(row["wholeFront"]["IGDplus"], old[seed, arm]["IGDplus"], rtol=1e-12, atol=1e-12)
                results.append({"stem": stem, "seed": seed, "arm": arm, "endpointFE": endpoint, **row})
    return {"source": str(source), "phase": phase, "partitions": results}

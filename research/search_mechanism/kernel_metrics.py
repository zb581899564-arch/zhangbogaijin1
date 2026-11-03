"""H2 matched-parent kernel metrics against one fixed, paid reference archive."""
from collections import defaultdict
import json
import math
from statistics import mean, median

import numpy as np

from research.dynamic_benchmark.metrics import hypervolume, nondominated
from .retention import covered_by, encoding, normalize, objective, points

KERNELS = ("PAPER", "JOB_ALIGNED", "CLASSIC_GLOBAL", "CLASSIC_PERSONAL")
IDENTITY = ("instance", "origin", "phase", "caseId")


def _signature(record):
    reference = np.unique(points(record["reference"]), axis=0).tolist()
    parent = {"encoding": encoding(record["parent"]), "objectives": objective(record["parent"]).tolist()}
    guides = {key: record.get(key) for key in ("personal", "global")}
    return json.dumps({"reference": reference, "parent": parent, **guides}, sort_keys=True)


def validate_pairing(records, replicates, kernels=KERNELS, expected_cases=None):
    """Reject missing cells before computing a favorable partial comparison."""
    replicates = list(range(replicates)) if isinstance(replicates, int) else list(replicates)
    if not replicates or len(set(replicates)) != len(replicates):
        raise ValueError("Fixed kernel replicate list must be nonempty and unique")
    if len(set(kernels)) != len(kernels) or set(kernels) != set(KERNELS):
        raise ValueError("All four predeclared kernels are required")
    expected = {(kernel, rep) for kernel in kernels for rep in replicates}
    groups = defaultdict(list)
    for record in records:
        identity = tuple(record[key] for key in IDENTITY)
        groups[identity].append(record)
    if expected_cases is not None and set(groups) != set(expected_cases):
        raise ValueError("Missing or unexpected frozen kernel cases")
    if not groups:
        raise ValueError("No kernel-case results")
    for identity, group in groups.items():
        cells = [(record["kernel"], record["rep"]) for record in group]
        if len(cells) != len(set(cells)) or set(cells) != expected:
            missing, extra = expected - set(cells), set(cells) - expected
            raise ValueError(f"Incomplete kernel pairing {identity}: missing={missing}, extra={extra}")
        if len({_signature(record) for record in group}) != 1:
            raise ValueError("Paired kernels changed their parent, guides or reference archive")
        for record in group:
            for field in ("generationNanos", "evaluationNanos"):
                value = record[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError("Missing or invalid kernel cost: " + field)
            if record.get("status", "passed").lower() not in ("passed", "success", "completed"):
                raise ValueError("Failed kernel result remains unresolved")
            if int(record["successfulFE"]) < 1:
                raise ValueError("Kernel evaluation was not paid")
    return groups


def case_metrics(record, normalization, reference=(1.5, 1.5, 1.5), prepared=None):
    archive = normalize(record["reference"], normalization) if prepared is None else prepared[0]
    if not len(archive):
        raise ValueError("Kernel reference archive must be nonempty")
    child = record.get("child")
    children = record.get("children", [child] if child is not None else [])
    if not children:
        raise ValueError("Kernel result contains no paid child")
    if child is None:
        if len(children) != 1:
            raise ValueError("A paid batch needs an explicit designated child for candidate metrics")
        child = children[0]
    parent = normalize([objective(record["parent"])], normalization)
    candidate = normalize([objective(child)], normalization)
    batch = normalize([objective(item) for item in children], normalization)
    # Compare candidate and whole paid batch to exactly the same pre-update archive.
    base = hypervolume(archive, reference) if prepared is None else prepared[1]
    candidate_gain = hypervolume(np.concatenate((archive, candidate)), reference) - base
    batch_gain = hypervolume(np.concatenate((archive, batch)), reference) - base
    if min(candidate_gain, batch_gain) < -1e-10:
        raise ValueError("HV union monotonicity failed for a kernel case")
    result = {key: record[key] for key in (*IDENTITY, "kernel", "rep", "seed", "successfulFE")}
    generation = record["generationNanos"] / 1e9
    evaluation = record["evaluationNanos"] / 1e9
    result.update({"referenceSize": len(record['reference']), "referenceNDSize": len(archive), "referenceHV": base,
                   "candidateDeltaHV": max(0., candidate_gain), "batchDeltaHV": max(0., batch_gain),
                   "paidBatchSize": len(batch),
                   "candidateDominatesParent": bool(covered_by(parent, candidate, strict=True)[0]),
                   "candidateDominatedByParent": bool(covered_by(candidate, parent, strict=True)[0]),
                   "candidateCoveredByReference": bool(covered_by(candidate, archive)[0]),
                   "candidateEqualParentObjectives": bool(np.array_equal(candidate[0], parent[0])),
                   "candidateSameParentGenotype": encoding(child) == encoding(record["parent"]),
                   "generationSeconds": generation, "evaluationSeconds": evaluation,
                   "generationEvaluationSeconds": generation + evaluation,
                   "repairChanged": record.get("repairChanged"), "changesByJob": record.get("changesByJob")})
    return result


def _aggregate(group, identity, keys):
    result = dict(zip(keys, identity)) | {"matchedEvaluations": len(group),
                                        "cases": len({tuple(row[key] for key in IDENTITY) for row in group})}
    for field in ("candidateDeltaHV", "batchDeltaHV", "generationSeconds", "evaluationSeconds",
                  "generationEvaluationSeconds", "paidBatchSize", "successfulFE"):
        values = [row[field] for row in group]
        result[field + "Mean"] = mean(values)
        result[field + "Median"] = median(values)
    for field in ("candidateDominatesParent", "candidateDominatedByParent", "candidateCoveredByReference",
                  "candidateEqualParentObjectives", "candidateSameParentGenotype"):
        result[field + "Rate"] = mean(int(row[field]) for row in group)
    result["candidatePositiveDeltaHVRate"] = mean(int(row["candidateDeltaHV"] > 1e-12) for row in group)
    repairs = [row["repairChanged"] for row in group if row["repairChanged"] is not None]
    result["repairChangedRate"] = mean(int(value) for value in repairs) if repairs else None
    result["totalGenerationEvaluationSeconds"] = sum(row["generationEvaluationSeconds"] for row in group)
    return result


def summarize_kernels(rows):
    output = []
    # No pooling across origin/phase for the principal comparison.
    for keys in (("instance", "origin", "phase", "kernel"), ("origin", "phase", "kernel")):
        groups = defaultdict(list)
        for row in rows:
            groups[tuple(row[key] for key in keys)].append(row)
        for identity, group in sorted(groups.items(), key=lambda item: str(item[0])):
            output.append({"stratum": "/".join(keys), **_aggregate(group, identity, keys)})
    return output


def paired_contrasts(rows):
    index = {tuple(row[key] for key in (*IDENTITY, "rep", "kernel")): row for row in rows}
    contrasts = []
    for key, baseline in index.items():
        if baseline["kernel"] != "PAPER":
            continue
        for kernel in KERNELS:
            if kernel == "PAPER":
                continue
            candidate = index[key[:-1] + (kernel,)]
            row = {field: baseline[field] for field in (*IDENTITY, "rep")}
            row.update({"candidate": kernel, "comparator": "PAPER"})
            for field in ("candidateDeltaHV", "batchDeltaHV", "generationEvaluationSeconds"):
                row[field + "Difference"] = candidate[field] - baseline[field]
            for field in ("candidateDominatesParent", "candidateDominatedByParent"):
                row[field + "Difference"] = int(candidate[field]) - int(baseline[field])
            contrasts.append(row)
    return contrasts


def summarize_contrasts(rows):
    groups = defaultdict(list)
    keys = ("instance", "origin", "phase", "candidate", "comparator")
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for identity, group in sorted(groups.items(), key=lambda item: str(item[0])):
        record = dict(zip(keys, identity)) | {"matchedPairs": len(group)}
        for field in ("candidateDeltaHVDifference", "batchDeltaHVDifference", "generationEvaluationSecondsDifference",
                      "candidateDominatesParentDifference", "candidateDominatedByParentDifference"):
            record[field + "Mean"] = mean(row[field] for row in group)
            record[field + "Median"] = median(row[field] for row in group)
        output.append(record)
    return output

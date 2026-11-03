"""Recover exact per-job FA contexts and partition paid returned archives."""
import json
import numpy as np
from research.dynamic_benchmark.metrics import hypervolume
from .physical import safe_bound


def family_contexts(requests, model):
    families = {}
    for request in requests:
        fa = [-1] * model["jobs"]
        for factory in request["factories"]:
            for job in factory["parent"]["jobs"]:
                if fa[job] != -1:
                    raise ValueError("Overlapping family context")
                fa[job] = factory["factory"]
            expected = sorted(factory["parent"]["jobs"])
            if any(sorted(record["jobs"]) != expected for record in factory["records"]):
                raise ValueError("Pool record leaves its fixed FA context")
        fa = tuple(fa); safe_bound(model, fa)
        old = families.setdefault(request["family"], fa)
        if old != fa:
            raise ValueError("Family FA changed in a frozen baseline")
    return families


def per_job_fa(solution, jobs):
    if sorted(solution["JS"]) != list(range(jobs)) or len(solution["FA"]) != jobs:
        raise ValueError("Malformed archived position-aligned JS/FA")
    fa = [-1] * jobs
    for job, factory in zip(solution["JS"], solution["FA"]):
        fa[job] = factory
    return tuple(fa)


def archive_coverage(folder, identity, families, spec, model, sources):
    path = folder / "solutions.jsonl"; solutions = sources.lines(path)
    summary = sources.json(folder / "summary.json")
    checkpoints = sources.lines(folder / "anytime.jsonl")
    final = [row for row in checkpoints if row["checkpointKind"] == "TIME" and row["checkpoint"] == spec["time_seconds"]]
    if len(final) != 1 or not final[0].get("reached", True) or final[0]["elapsedSeconds"] > spec["time_seconds"] + 1e-9:
        raise ValueError("Missing deadline-valid returned archive")
    if len(solutions) != summary["archiveSize"]:
        raise ValueError("Incomplete paid returned solutions")
    returned = {tuple(row["objectives"]) for row in solutions}; cutoff = {tuple(row) for row in final[0]["front"]}
    unknown = len(cutoff - returned); excluded = len(returned - cutoff)
    solutions = [row for row in solutions if tuple(row["objectives"]) in cutoff]
    if not solutions:
        raise ValueError("No encoded solutions match the valid cutoff front")
    scale = np.asarray(spec["normalization"]["scale"]); low = np.asarray(spec["normalization"]["lower"])
    contexts = [per_job_fa(row, model["jobs"]) for row in solutions]
    members = [fa in families.values() for fa in contexts]
    objectives = np.asarray([row["objectives"] for row in solutions]); normalized = (objectives - low) / scale
    def hv(mask):
        return hypervolume(normalized[np.asarray(mask, dtype=bool)], [1.5] * 3)
    known_hv = hypervolume(normalized, [1.5] * 3)
    all_hv = hypervolume((np.asarray(final[0]["front"]) - low) / scale, [1.5] * 3)
    family_hv = hv(members); other_hv = hv([not member for member in members])
    row = identity | {"archiveSolutions": len(cutoff), "encodedCutoffSolutions": len(solutions),
        "cutoffUnknownEncodings": unknown, "returnedObjectivesExcludedFromCutoff": excluded,
        "knownCutoffHVFraction": known_hv / all_hv if all_hv else None, "uniqueFA": len(set(contexts)),
        "matchedFamilySolutions": sum(members), "nonFamilySolutions": len(solutions) - sum(members),
        "matchedFamilyUniqueFA": len({fa for fa, member in zip(contexts, members) if member}),
        "nonFamilyUniqueFA": len({fa for fa, member in zip(contexts, members) if not member}),
        "matchedSolutionFraction": sum(members) / len(cutoff), "allHV": all_hv,
        "matchedFamilyHV": family_hv, "nonFamilyHV": other_hv,
        "matchedFamilyHVFraction": family_hv / all_hv if all_hv else None,
        "nonFamilyExclusiveHVFraction": (all_hv - family_hv) / all_hv if all_hv and unknown == 0 else None,
        "familyExclusiveHVFraction": (all_hv - other_hv) / all_hv if all_hv and unknown == 0 else None,
        "source": str(path)}
    per_family = []
    for family, fa in families.items():
        mask = [context == fa for context in contexts]
        per_family.append(identity | {"family": family, "solutions": sum(mask), "HV": hv(mask),
            "perJobFA": json.dumps(fa), "source": str(path)})
    diversity = []
    for fa in sorted(set(contexts)):
        mask = [context == fa for context in contexts]
        diversity.append(identity | {"perJobFA": json.dumps(fa), "matchingFamilies": "+".join(str(f) for f, value in families.items() if value == fa),
            "solutions": sum(mask), "HV": hv(mask), "source": str(path)})
    return row, per_family, diversity

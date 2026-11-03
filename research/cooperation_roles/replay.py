"""Numeric retained-pool replay only: never decodes or evaluates a schedule."""
import math
from .protocol import PHYSICAL_ROLES


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


def vector(values):
    if not isinstance(values, list) or len(values) != 3 or any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Malformed nonnegative physical objective triple")
    return values


def score(objectives, request):
    return objectives[1] / request["energyScale"] + request["eta"] * objectives[2] / request["wageScale"]


def encoding(record):
    return tuple(tuple(record[key]) for key in ("jobs", "machines", "workers"))


def validate_record(record, parent, request, *, paid=True):
    vector(record["objectives"]); vector(record["wholeObjectives"])
    arrays = [record[key] for key in ("jobs", "machines", "workers")]
    if not arrays[0] or len({len(values) for values in arrays}) != 1:
        raise ValueError("Empty or unaligned local record")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for values in arrays for value in values):
        raise ValueError("Invalid local resource/job identifier")
    if len(set(arrays[0])) != len(arrays[0]) or sorted(arrays[0]) != sorted(parent["jobs"]):
        raise ValueError("Factory record escapes fixed FA context")
    if paid and (not isinstance(record["paidFE"], int) or not 1 <= record["paidFE"] <= request["proposalFE"]):
        raise ValueError("Retained record has future or unpaid provenance")
    if paid and (not 0 <= record["generation"] <= request["generation"] or record["producer"] not in (*PHYSICAL_ROLES, "INITIALIZATION")):
        raise ValueError("Invalid retained-record source/generation")
    if any(a > b and not close(a, b) for a, b in zip(record["objectives"], record["wholeObjectives"])):
        raise ValueError("Local contribution exceeds its paid whole source")


def choose(records, request, excluded=None):
    # Strict improvement preserves the Java list's first equal-score record.
    best, value = None, math.inf
    for record in records:
        if record["producer"] == excluded or record["objectives"][0] > request["cap"]:
            continue
        candidate = score(record["objectives"], request)
        if candidate < value:
            best, value = record, candidate
    return best


def assemble(records):
    if any(record is None for record in records):
        return None
    result = [0., 0., 0.]
    for record in records:
        result[0] = max(result[0], record["objectives"][0])
        result[1] += record["objectives"][1]; result[2] += record["objectives"][2]
    return result


def gain(baseline, candidate):
    return (baseline - candidate) / baseline if baseline > 0 else None


def request_replay(request):
    vector(request["parentObjectives"])
    for key in ("cap", "energyScale", "wageScale"):
        if not math.isfinite(request[key]) or request[key] <= 0:
            raise ValueError("Nonpositive cap/normalization scale")
    if not 0 <= request["cycle"] < 9 or request["eta"] != (0, 1, 4)[request["cycle"] % 3]:
        raise ValueError("Composition cycle or eta changed")
    if not close(request["cap"], request["parentObjectives"][0] * (.9, 1, 1.1)[request["cycle"] // 3]):
        raise ValueError("Composition cap cycle changed")
    factories = request["factories"]
    if [factory["factory"] for factory in factories] != list(range(len(factories))):
        raise ValueError("Factory order must preserve Java summation order")
    chosen, all_records, job_sets = [], [], []
    for factory in factories:
        parent = factory["parent"]; records = factory["records"]
        validate_record(parent, parent, request, paid=False)
        if len(records) > 8:
            raise ValueError("Retained pool escaped capacity8")
        for record in records:
            validate_record(record, parent, request)
        selected = choose(records, request)
        if selected != factory["chosen"]:
            raise ValueError("Captured choose differs from independent pool replay")
        chosen.append(selected); all_records.extend(records); job_sets.extend(parent["jobs"])
    if len(job_sets) != len(set(job_sets)):
        raise ValueError("Factory contexts overlap")
    reconstructed_parent = assemble([factory["parent"] for factory in factories])
    if not all(close(a, b) for a, b in zip(reconstructed_parent, request["parentObjectives"])):
        raise ValueError("Parent factory contributions do not reconstruct its objectives")
    wholes = {}
    for record in all_records:
        prior = wholes.setdefault(record["paidFE"], record["wholeObjectives"])
        if not all(close(a, b) for a, b in zip(prior, record["wholeObjectives"])):
            raise ValueError("A paid evaluation carries inconsistent whole objectives")
    combined = assemble(chosen); feasible = combined is not None
    if feasible != request["feasible"] or (combined is None) != (request["combinedObjectives"] is None):
        raise ValueError("Captured feasibility differs from numeric replay")
    if feasible and not all(close(a, b) for a, b in zip(combined, vector(request["combinedObjectives"]))):
        raise ValueError("Whole-factory composition objective replay failed")
    same = feasible and all(encoding(record) == encoding(factory["parent"]) for record, factory in zip(chosen, factories))
    outcome = "INFEASIBLE" if not feasible else "DUPLICATE_PARENT" if same else "PROPOSED"
    if outcome != request["outcome"]:
        raise ValueError("Composition outcome disagrees with local-encoding replay")
    parent_score = score(request["parentObjectives"], request)
    combined_score = score(combined, request) if feasible else None
    parent_gain = gain(parent_score, combined_score) if feasible else None
    if feasible and not close(parent_gain if parent_gain is not None else 0., request["weightedRelativeImprovement"]):
        raise ValueError("Captured weighted parent improvement differs")
    if not feasible and request["weightedRelativeImprovement"] is not None:
        raise ValueError("Infeasible request fabricated an improvement")
    whole_scores = [score(record["wholeObjectives"], request) for record in all_records
                    if record["wholeObjectives"][0] <= request["cap"]]
    best_whole = min(whole_scores) if whole_scores else None
    whole_gain = gain(best_whole, combined_score) if feasible and best_whole is not None else None
    paid_sources = {record["paidFE"] for record in chosen if record is not None}
    producers = {record["producer"] for record in chosen if record is not None}
    complementary = feasible and len(paid_sources) >= 2 and parent_gain is not None and parent_gain >= .001 and whole_gain is not None and whole_gain >= .001
    return {"request": request["request"], "family": request["family"], "generation": request["generation"],
        "proposalFE": request["proposalFE"], "cycle": request["cycle"], "tight": request["cycle"] < 3,
        "feasible": feasible, "outcome": outcome, "missingFactories": sum(record is None for record in chosen),
        "distinctChosenPaidFE": len(paid_sources), "distinctChosenProducers": len(producers),
        "distinctChosenSearchProducers": len(producers - {"INITIALIZATION"}),
        "chosenProducerSignature": "+".join(sorted(producers)),
        "parentScore": parent_score, "combinedScore": combined_score, "bestFeasibleWholeScore": best_whole,
        "parentRelativeGain": parent_gain, "bestWholeRelativeGain": whole_gain,
        "genuineComplementarity": complementary,
        "feasibilityCompletionWithoutWholeBaseline": feasible and best_whole is None}


def withdrawals(request):
    """Label dependence of the captured retained pool, never deleting a group."""
    baseline = assemble([choose(factory["records"], request) for factory in request["factories"]])
    baseline_score = score(baseline, request) if baseline is not None else None
    result = []
    for producer in (*PHYSICAL_ROLES, "INITIALIZATION"):
        selected = [choose(factory["records"], request, producer) for factory in request["factories"]]
        candidate = assemble(selected)
        candidate_score = score(candidate, request) if candidate is not None else None
        result.append({"request": request["request"], "removedProducer": producer,
            "baselineFeasible": baseline is not None, "withdrawalFeasible": candidate is not None,
            "baselineScore": baseline_score, "withdrawalScore": candidate_score,
            "relativeScoreIncrease": (candidate_score - baseline_score) / baseline_score
                if baseline_score is not None and baseline_score > 0 and candidate_score is not None else None,
            "interpretation": "captured retained-label dependence; not whole-group causal effect"})
    return result

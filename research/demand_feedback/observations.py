"""Independent fixed-routing replay and additive controller validation costs."""
import math
from pathlib import Path
from research.semantic_repair.evidence import read
from research.semantic_repair.trials import json_lines
from research.cooperation_roles.observations import load_run as shared_load_run

MODES = {"SHARE_SPECIAL": None, "SHARE_DEMAND_SPECIAL": "DEMAND", "SHARE_SHAM_SPECIAL": "SHAM"}


def target(minima, cap):
    if not math.isfinite(cap) or cap <= 0 or not minima or any(not math.isfinite(value) or value < 0 for value in minima):
        raise ValueError("Malformed current factory minima/cap")
    selected, largest = -1, 0.
    for factory, minimum in enumerate(minima):
        deficit = (minimum - cap) / cap
        if deficit > largest:
            selected, largest = factory, deficit
    return selected


def replay_query(row, mode, summary, pool_trace):
    factories = int(Path(summary["instance"]).stem.split("_")[2])
    limit = summary["timeLimitSeconds"] if summary["timeLimitSeconds"] is not None else math.inf
    if row.get("type") != "demand-local-query" or row.get("deadlineValid") is not True or not 0 <= row["elapsedSeconds"] <= limit:
        raise ValueError("Late or malformed demand query")
    if row["physicalGroup"] != "MAKESPAN" or not 0 <= row["family"] < 4:
        raise ValueError("Demand routing escaped physical MAKESPAN FA families")
    if not 1 <= row["requestFE"] <= row["queryFE"] <= summary["successful"]:
        raise ValueError("Demand request/query references future or unpaid FE")
    if not 1 <= row["requestGeneration"] <= row["generation"] <= summary["cooperation"]["compositionTiming"]["generationsStarted"]:
        raise ValueError("Demand request/query generation is in the future")
    if len(row["factoryMinC"]) != factories or not 0 <= row["randomFactory"] < factories:
        raise ValueError("Demand query factory count/index differs from instance")
    replayed = target(row["factoryMinC"], row["cap"])
    selected = replayed if mode == "DEMAND" and replayed >= 0 else row["randomFactory"]
    if row["targetFactory"] != replayed or row["selectedFactory"] != selected:
        raise ValueError("Independent max-gap target/routing replay failed")
    matches = [request for request in (pool_trace or [])[1:] if request["family"] == row["family"] and request["proposalFE"] == row["requestFE"]]
    for request in matches:
        if request["cycle"] >= 3 or request["generation"] != row["requestGeneration"] or not math.isclose(request["cap"], row["cap"], rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("Demand cap metadata differs from captured tight request")
    return {**row, "replayedTargetFactory": replayed, "replayedSelectedFactory": selected,
        "actionable": replayed >= 0, "overrodeRandomFactory": selected != row["randomFactory"],
        "matchedCapturedTightRequest": bool(matches), "requestAgeFE": row["queryFE"] - row["requestFE"],
        "maxPositiveRelativeGap": max(0., max((value - row["cap"]) / row["cap"] for value in row["factoryMinC"])),
        "interpretation": "Query/routing event, not proof of a subsequent paid VNS candidate or final HV contribution"}


def validate_demand(folder, summary, label, pool_trace=None):
    mode = MODES[label]; data = summary["cooperation"].get("demandFeedback")
    path = folder / "demand-trace.jsonl"
    if mode is None:
        if data is not None or path.exists():
            raise ValueError("Original SHARE acquired demand manager/trace")
        return None, []
    trace = json_lines(path)
    if not isinstance(data, dict) or not trace or trace[0] != dict(data, type="demand-feedback-summary"):
        raise ValueError("Demand trace/header mismatch")
    if data.get("mode") != mode or data.get("queryIsNotPaidCandidate") is not True or data.get("extraFE") != 0 or data.get("extraRNG") != 0:
        raise ValueError("Demand mode or zero-extra-FE/RNG contract differs")
    fields = ("tightRequestsRecorded", "queries", "eligibleQueries", "actionableQueries", "routedOverrides", "resolvedOrNoGapQueries")
    if any(type(data.get(key)) is not int or data[key] < 0 for key in fields):
        raise ValueError("Missing complete nonnegative demand counters")
    if not (data["actionableQueries"] + data["resolvedOrNoGapQueries"] == data["eligibleQueries"] <= data["queries"]
            and data["routedOverrides"] <= data["actionableQueries"]):
        raise ValueError("Inconsistent full query/gap/override counters")
    if mode == "SHAM" and data["routedOverrides"] != 0:
        raise ValueError("SHAM changed the original random factory")
    if data["eligibleQueries"] and not data["tightRequestsRecorded"]:
        raise ValueError("Eligible query without a previously recorded tight request")
    count = data["eligibleQueries"]
    expected = list(range(1, min(count, 8) + 1)) + list(range(max(9, count - 7), count + 1))
    if [row.get("eligibleQuery") for row in trace[1:]] != expected:
        raise ValueError("First8+last8 eligible-query policy changed")
    queries = [row["query"] for row in trace[1:]]
    if queries != sorted(set(queries)) or any(not 1 <= value <= data["queries"] for value in queries):
        raise ValueError("Global query numbering is not increasing/bounded")
    replays = [replay_query(row, mode, summary, pool_trace) for row in trace[1:]]
    if sum(row["actionable"] for row in replays) > data["actionableQueries"] or sum(row["overrodeRandomFactory"] for row in replays) > data["routedOverrides"]:
        raise ValueError("Captured demand events exceed full counters")
    return trace, replays


def attach_demand(run, folder):
    run["demandTrace"], run["demandReplay"] = validate_demand(folder, run["summary"], run["variant"], run.get("poolTrace"))


def apply_validation_receipt(run, receipt):
    seconds = receipt.get("additionalControllerValidationSeconds")
    if receipt.get("status") != "passed" or receipt.get("extraFE") != 0 or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Missing demand validation cost receipt")
    if run.get("demandValidationIncluded"):
        raise ValueError("Demand validation cost cannot be added twice")
    execution = dict(run["execution"])
    execution["baseControllerValidationSeconds"] = execution["controllerValidationSeconds"]
    execution["demandControllerValidationSeconds"] = seconds
    execution["controllerValidationSeconds"] += seconds
    run["execution"] = execution; run["demandValidationIncluded"] = True


def load_run(root, job, instance, spec):
    run = shared_load_run(root, job, instance, spec)
    folder = Path(run["folder"]); attach_demand(run, folder)
    apply_validation_receipt(run, read(folder / "demand-validation.json"))
    return run

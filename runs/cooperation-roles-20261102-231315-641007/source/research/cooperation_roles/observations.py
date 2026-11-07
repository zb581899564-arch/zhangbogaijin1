"""Validate all common evidence and effective/physical role separation."""
from pathlib import Path
from research.center_last.observations import validate_observations
from research.semantic_repair.trials import json_lines, load_trial
from .protocol import PHYSICAL_ROLES, trial_folder
from .replay import request_replay, withdrawals


def validate_roles(summary, label):
    if label == "NSGA":
        return
    co, search = summary["cooperation"], summary["search"]
    special = label.endswith("SPECIAL")
    expected = {role: role if special else "CENTER" for role in PHYSICAL_ROLES}
    if co.get("targetSpecialization") is not special or co.get("rolePreferenceMap") != expected:
        raise ValueError("Wrong effective preference factor or physical group map")
    complete = search.get("generations.completed", 0)
    for group, role in enumerate(PHYSICAL_ROLES, 1):
        updates = search.get(f"qgs.g{group}.updates", 0)
        if not complete * 50 <= updates <= (complete + 1) * 50:
            raise ValueError("Changed physical QGS step budget")
        if search.get(f"qgs.g{group}.preference.{expected[role]}", 0) != updates:
            raise ValueError("QGS effective preference was not used")
        for other in PHYSICAL_ROLES:
            if other != expected[role] and search.get(f"qgs.g{group}.preference.{other}", 0):
                raise ValueError("Unregistered role preference counter")
        local_count = sum(search.get(f"local.g{group}.preference.{other}", 0) for other in PHYSICAL_ROLES)
        if (complete or local_count) and search.get(f"local.g{group}.preference.{expected[role]}", 0) < 1:
            raise ValueError("Registered local-search preference never used")
        if any(search.get(f"local.g{group}.preference.{other}", 0) for other in PHYSICAL_ROLES if other != expected[role]):
            raise ValueError("Unregistered local-search role preference")


def validate_pool_trace(folder, summary, label):
    if label == "NSGA":
        if (folder / "cooperation-evidence.jsonl").exists():
            raise ValueError("NSGA acquired a cooperation pool observer")
        return None, [], []
    trace = json_lines(folder / "cooperation-evidence.jsonl")
    header = summary["cooperation"].get("poolEvidence")
    if not isinstance(header, dict) or not trace or trace[0] != dict(header, type="cooperation-evidence-summary"):
        raise ValueError("Missing or mismatched retained-pool evidence header")
    if header.get("extraFE") != 0 or header.get("consumesRNG") is not False:
        raise ValueError("Pool observation consumed FE or RNG")
    keys = ("requests", "tightRequests", "tightRequestsMissingFactory", "feasibleRequests", "weightedImprovementAtLeast001")
    if any(not isinstance(header.get(key), int) or header[key] < 0 for key in keys):
        raise ValueError("Missing complete nonnegative request counters")
    total = header["requests"]
    if not (header["tightRequestsMissingFactory"] <= header["tightRequests"] <= total and
            header["weightedImprovementAtLeast001"] <= header["feasibleRequests"] <= total):
        raise ValueError("Inconsistent full request counters")
    co = summary["cooperation"]
    if total > co.get("assemblyRequests", 0) or (label.startswith("SYNC") and total):
        raise ValueError("Evidence requests are not deadline-valid real shared requests")
    expected = list(range(1, min(total, 8) + 1)) + list(range(max(9, total - 7), total + 1))
    if [row.get("request") for row in trace[1:]] != expected:
        raise ValueError("First8+last8 bounded request policy changed")
    limit = summary["timeLimitSeconds"] if summary["timeLimitSeconds"] is not None else float("inf")
    replays, removed = [], []
    instance = Path(summary["instance"]).stem.split("_")
    for row in trace[1:]:
        if row.get("type") != "retained-pool-request" or row.get("deadlineValid") is not True or not 0 <= row["elapsedSeconds"] <= limit:
            raise ValueError("Late or malformed pool request")
        if not 0 <= row["family"] < 4 or not 0 <= row["proposalFE"] <= summary["successful"]:
            raise ValueError("Invalid family or future request")
        replay = request_replay(row)
        jobs = [job for factory in row["factories"] for job in factory["parent"]["jobs"]]
        if len(row["factories"]) != int(instance[2]) or sorted(jobs) != list(range(int(instance[0]))):
            raise ValueError("Request omitted instance factories or jobs")
        replays.append(replay); removed.extend(withdrawals(row))
    return trace, replays, removed


def load_run(root, job, instance, spec):
    folder = trial_folder(root, job)
    run = load_trial(folder, instance, job["seed"], job["variant"], spec)
    run["feedbackTrace"], run["compositionTrace"] = validate_observations(
        folder, run["summary"], job["variant"], require_complete=False)
    validate_roles(run["summary"], job["variant"])
    run["poolTrace"], run["poolReplay"], run["poolWithdrawals"] = validate_pool_trace(folder, run["summary"], job["variant"])
    return run

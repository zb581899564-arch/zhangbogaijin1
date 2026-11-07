"""Offline deadline-valid metrics. Empirical reference construction never feeds search."""
import json
from pathlib import Path
import numpy as np
from research.dynamic_benchmark.io import csv_write
from research.dynamic_benchmark.metrics import hypervolume, igd_plus, nondominated
from .execution import read, write


def _point(rows, kind, checkpoint):
    matches = [r for r in rows if r["checkpointKind"] == kind and abs(r["checkpoint"]-checkpoint) < 1e-9]
    if len(matches) != 1:
        raise ValueError("Missing or duplicate checkpoint: " + kind + " " + str(checkpoint))
    return matches[0]


def _front(row, seconds, scale):
    if row.get("reached", True):
        if row["elapsedSeconds"] > seconds + 1e-9:
            raise ValueError("Future archive entered a deadline-valid snapshot")
        result = np.asarray(row["front"], dtype=float).reshape(-1, 3)
        if not len(result) or not np.isfinite(result).all():
            raise ValueError("Empty or nonfinite paid archive")
        return result / scale
    if row["front"]:
        raise ValueError("Censored checkpoint has a fabricated front")
    return None


def load_trial(folder, instance, seed, variant, seconds):
    summary = read(folder / "summary.json")
    if summary["status"] != "passed" or summary["failed"] != summary["timeInterruptedAttempts"]:
        raise ValueError("Run invalid: " + str(folder))
    if summary["stopReason"] != "TIME_LIMIT" or abs(summary["timeLimitSeconds"]-seconds) > 1e-9:
        raise ValueError("Wrong registered budget: " + str(folder))
    rows = [json.loads(line) for line in (folder/"anytime.jsonl").read_text(encoding="utf-8").splitlines()]
    scale = np.asarray(instance["normalization"]["scale"])
    final = _point(rows, "TIME", seconds)
    half = _point(rows, "TIME", seconds/2)
    fe = _point(rows, "FE", 15000)
    if fe.get("reached", True) and fe["fe"] != 15000:
        raise ValueError("Fixed-FE snapshot included a future successful evaluation")
    return {"instance":instance["stem"], "seed":seed, "variant":variant, "summary":summary,
            "final":_front(final, seconds, scale), "half":_front(half, seconds/2, scale),
            "fe":_front(fe, seconds, scale), "finalRow":final, "feRow":fe}


def _cost_row(run):
    s = run["summary"]
    joint, coop = s.get("joint", {}), s.get("cooperation", {})
    return {"instance":run["instance"], "seed":run["seed"], "variant":run["variant"],
            "attempted":s["attempted"], "successful":s["successful"], "deadlineValidFE":run["finalRow"]["fe"],
            "searchSeconds":s["searchSeconds"], "overshootSeconds":s["deadlineOvershootSeconds"],
            "interruptedAttempts":s["timeInterruptedAttempts"], "archiveSize":len(run["final"]),
            "offlineValidationDecodes":s["offlineValidationDecodes"],
            "fixedFEReached":run["fe"] is not None,
            "decodeSeconds":s["decoder"]["dynamic.decodeNanos"]/1e9,
            "guidedTrajectories":joint.get("completedTrajectories", 0),
            "proposeSeconds":joint.get("proposeNanos", 0)/1e9,
            "trainingSeconds":joint.get("trainingNanos", 0)/1e9,
            "cooperationSeconds":coop.get("cooperationSeconds", 0),
            "assemblies":coop.get("assembliesValidated", 0),
            "classicSetting":s.get("classicSetting", 0)}


def metric_records(runs, references):
    records, costs = [], []
    for run in runs:
        record = {k:run[k] for k in ["instance", "seed", "variant"]}
        record["hv"] = {str(p):hypervolume(run["final"], [p]*3) for p in [1.25, 1.5, 2.0]}
        record["igdplus"] = igd_plus(run["final"], references[run["instance"]])
        record["hv_half"] = hypervolume(run["half"], [1.5]*3)
        record["hv_fe15000"] = None if run["fe"] is None else hypervolume(run["fe"], [1.5]*3)
        records.append(record)
        cost = _cost_row(run)
        for point in [1.25, 1.5, 2.0]:
            cost["HV_"+str(point)] = record["hv"][str(point)]
            cost["outside_"+str(point)] = int(np.any(run["final"] >= point, axis=1).sum())
        cost["IGDplus"] = record["igdplus"]
        costs.append(cost)
    return records, costs


def analyze(root, policy, *, phase="initial", candidate=None, external=None):
    output = root / "analysis" / phase
    output.mkdir(parents=True)
    seeds = policy["algorithm_seeds"] if phase == "initial" else policy["followup"]["seeds"]
    variants = policy["variants"] if phase == "initial" else [candidate, "BASELINE", external]
    multiplier = 1 if phase == "initial" else policy["followup"]["time_multiplier"]
    runs = []
    for instance in policy["instances"]:
        for seed in seeds:
            for variant in variants:
                folder = root / "trials" / phase / instance["stem"] / str(seed) / variant
                runs.append(load_trial(folder, instance, seed, variant, instance["time_seconds"]*multiplier))
    references = {}
    for instance in policy["instances"]:
        stem = instance["stem"]
        if phase == "initial":
            references[stem] = nondominated(np.concatenate([r["final"] for r in runs if r["instance"] == stem]))
            write(output/(stem+"-reference.json"), references[stem].tolist(), once=True)
        else:
            references[stem] = np.asarray(read(root/"analysis/initial"/(stem+"-reference.json")))
    records, costs = metric_records(runs, references)
    write(output/"records.json", records, once=True)
    csv_write(output/"run-metrics.csv", costs)
    audit = {"status":"passed", "runs":len(runs), "genuineFailures":0,
             "attempted":sum(c["attempted"] for c in costs), "successful":sum(c["successful"] for c in costs),
             "timeInterruptedAttempts":sum(c["interruptedAttempts"] for c in costs),
             "maxOvershootSeconds":max(c["overshootSeconds"] for c in costs),
             "offlineValidationDecodes":sum(c["offlineValidationDecodes"] for c in costs),
             "assembliesValidated":sum(c["assemblies"] for c in costs),
             "fixedFEReached":sum(c["fixedFEReached"] for c in costs)}
    write(output/"audit.json", audit, once=True)
    return records

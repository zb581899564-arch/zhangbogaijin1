"""Completed working-population snapshots and duplicate-blocked folds; no decoder calls."""
from collections import Counter, defaultdict
import hashlib
import json

import numpy as np

from run_long_budget_bridge import rows
from pa_paid_donor_data import role


def physical_key(point):
    factories, keys = point["factories"], point["keys"]
    chains = [sorted([j for j, f in enumerate(factories) if f == factory], key=lambda j: (keys[j], j))
              for factory in range(max(factories) + 1)]
    return json.dumps([point["allocations"], chains], separators=(",", ":"))


def group_folds(points, kind):
    keys = [physical_key(p) if kind == "PHYSICAL" else json.dumps(p["factories"], separators=(",", ":"))
            for p in points]
    folds = np.asarray([int(hashlib.sha256((kind + key).encode()).hexdigest()[:8], 16) % 5 for key in keys])
    physical = [physical_key(p) for p in points]
    counts = Counter(physical)
    return folds, np.asarray([1. / counts[key] for key in physical])


def engineering_snapshots(folder, stem, mode):
    catalog, = rows(folder / "catalog.jsonl")
    tuples = catalog["tuples"]
    points, result = [], []
    with (folder / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            if event["kind"] == "reencode":
                assert event["slot"] == len(points)
                allocations = [tuples[r] for r in event["resources"]]
                points.append({"id": event["id"], "role": event["role"], "allocations": allocations,
                               "factories": [t[0] for t in allocations], "keys": event["keys"],
                               "objectives": event["objectives"]})
            elif event["kind"] == "model":
                assert len(points) == 100 and [p["id"] for p in points] == [p["id"] for p in event["population"]]
                result.append({"id": f"{stem}-ENGINE-{mode}-G{event['generation']}", "stem": stem,
                               "generation": event["generation"], "kind": "ENGINEERING",
                               "aliases": [str(folder)], "points": points})
                points = []
    assert len(result) == 2 and not points
    return result


def science_initial(folder, stem, seed):
    points = []
    for i, record in enumerate(rows(folder / "initial-population.jsonl")):
        jobs = len(record["JS"])
        allocations, keys = [None] * jobs, [None] * jobs
        for rank, (job, f, m, w) in enumerate(zip(record["JS"], record["FA"], record["MA"], record["WA"])):
            allocations[job], keys[job] = [f, m, w], (rank + .5) / jobs
        points.append({"role": role(i), "allocations": allocations, "factories": [t[0] for t in allocations],
                       "keys": keys, "objectives": record["objectives"]})
    assert len(points) == 100
    return {"id": f"{stem}-SCIENCE-INITIAL-{seed}", "stem": stem, "generation": 0,
            "kind": "SCIENCE_INITIAL", "aliases": [str(folder)], "points": points}


def snapshots(root, plan):
    result, seen = [], {}
    for spec in plan["instances"]:
        stem = spec["stem"]
        for mode in ("NONE", "GRAFT"):
            folder = root / stem / ("ENGINEERING-" + mode) / "audit"
            for snapshot in engineering_snapshots(folder, stem, mode):
                # First-generation NONE/GRAFT inputs are identical; do not count them twice.
                signature = json.dumps([stem, snapshot["generation"], snapshot["points"]], sort_keys=True)
                if signature in seen:
                    seen[signature]["aliases"].extend(snapshot["aliases"])
                else:
                    seen[signature] = snapshot
                    result.append(snapshot)
        for seed in plan["seeds"]:
            result.append(science_initial(root / stem / str(seed) / "SOURCE_S", stem, seed))
    assert len(result) == 10
    return result


def identifiability(points):
    strata = defaultdict(Counter)
    for point in points:
        strata[tuple(point["factories"])][point["role"]] += 1
    mixed = [counts for counts in strata.values() if len(counts) > 1]
    return {"factoryPatterns": len(strata), "physicalSchedules": len({physical_key(p) for p in points}),
            "crossRoleFactoryPatterns": len(mixed), "pointsInCrossRoleFactoryPatterns": sum(sum(c.values()) for c in mixed),
            "roleCounts": dict(Counter(p["role"] for p in points))}


def pair_data(points, factories, normalization):
    f = np.asarray([p["factories"] for p in points], int)
    keys = np.asarray([p["keys"] for p in points], float)
    a, b = np.triu_indices(f.shape[1], 1)
    assert len(a) and f.min() >= 0 and f.max() < factories
    objectives = (np.asarray([p["objectives"] for p in points]) - normalization["lower"]) / normalization["scale"]
    return {"codes": f[:, a] * factories + f[:, b], "same": f[:, a] == f[:, b],
            "before": keys[:, a] < keys[:, b], "labels": np.asarray([p["role"] for p in points]),
            "objectives": objectives, "factories": factories, "offset": np.arange(len(a)) * factories**2}

"""Reconstruct external physical deduplication and paid-source availability."""
from collections import Counter
import math

from analysis_common import read_json, require
from audit_genome import by_job, collect_catalog, physical, verify_encoding


def points_tsv(path):
    result = []
    with path.open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            fields = line.rstrip("\r\n").split("\t")
            require(len(fields) == 10, f"Expected 10 columns at {path}:{number}")
            source, index, paid, role, family = fields[:5]
            row = dict(source=source, index=int(index), paidByFE=int(paid), role=role,
                       family=int(family), objectives=[float(v) for v in fields[5].split(",")])
            for name, value in zip(("JS", "FA", "MA", "WA"), fields[6:]):
                row[name] = [int(v) for v in value.split(",")]
            require(len(row["objectives"]) == 3 and all(map(math.isfinite, row["objectives"])),
                    "Nonfinite captured objectives")
            require(source in ("P", "G", "S"), "Unknown captured source")
            result.append(row)
    return result


def capture_data(folder, jobs, factories):
    capture = read_json(folder / "capture.json")
    require(capture["passed"] is True and capture["beforeGlobalFE"] >= 250000,
            "Capture is not a mature successful block")
    require(capture["afterGlobalFE"] - capture["beforeGlobalFE"] == 5000
            and capture["globalPaidCandidates"] == 5000, "Global supply must be exactly 5000 paid points")
    rows = points_tsv(folder / "points.tsv")
    initial, global_rows = rows[:100], rows[100:]
    require(len(rows) == 5100 and all(r["source"] == "P" for r in initial), "Missing P100 or global5000")
    require([r["index"] for r in initial] == list(range(100)), "P slot registry differs")
    require([r["index"] for r in global_rows] == list(range(5000)), "Global ordinal registry differs")
    require(all(r["paidByFE"] == capture["beforeGlobalFE"] for r in initial), "P availability bound differs")
    require([r["paidByFE"] for r in global_rows] == list(range(capture["beforeGlobalFE"] + 1,
                                                              capture["afterGlobalFE"] + 1)),
            "Missing, duplicate, unordered or future paid global source")
    for row in rows:
        require(len(row["JS"]) == jobs and row["family"] in (-1, 0, 1, 2, 3), "Invalid job/family registry")
        fa = by_job(row, "FA")
        require(set(fa) == set(range(factories)), "Captured factory support is incomplete")
    source_counts = Counter(r["source"] for r in global_rows)
    require(source_counts["S"] == capture["sharedPaidCandidates"]
            and source_counts["G"] == capture["ordinaryPaidCandidates"], "Capture source counts disagree")
    expected = reconstruct_external(initial, global_rows, factories)
    return dict(receipt=capture, initial=initial, expectedExternal=expected,
                sourceCounts=dict(source_counts), background=read_json(folder / "background.json"))


def reconstruct_external(initial, global_rows, factories):
    initial_keys = {(r["family"], physical(r, factories)) for r in initial}
    unique = {}
    for row in global_rows:
        key = row["family"], physical(row, factories)
        if key in initial_keys:
            continue
        if key not in unique:
            unique[key] = dict(row)
        else:
            previous = unique[key]
            require(previous["objectives"] == row["objectives"], "Same paid physical schedule has different objectives")
            if row["source"] not in previous["source"]:
                previous["source"] = "GS"
    return list(unique.values())


def verify_imports(before, views, captured, jobs, factories):
    require(len(before) == 100 and [r["slot"] for r in before] == list(range(100)), "Wrong initial slots")
    families = Counter(r["family"] for r in before)
    require(families == {-1: 80, 0: 5, 1: 5, 2: 5, 3: 5}, "Mature receiver family quotas changed")
    require(Counter(r["role"] for r in before) == {"CENTER": 55, "MAKESPAN": 15, "ENERGY": 15, "WORKER_COST": 15},
            "Mature receiver role quotas changed")
    for actual, source in zip(before, captured["initial"]):
        require(all(actual[k] == source[k] for k in ("family", "role", "objectives")), "P receiver identity changed")
        require(physical(actual, factories) == physical(source, factories), "P receiver physical chain changed")
    require(len(views) == len(captured["expectedExternal"]), "External deduplicated view count differs")
    for index, (actual, source) in enumerate(zip(views, captured["expectedExternal"])):
        require(actual["id"] == index, "External IDs must follow first-paid insertion order")
        require(all(actual[k] == source[k] for k in ("family", "source", "paidByFE", "objectives")),
                "External provenance or GS overlap differs")
        require(physical(actual, factories) == physical(source, factories), "External reencoding changed physical chain")
    catalog = collect_catalog(before + views)
    fixed = {}
    for row in before + views:
        require(len(row["keys"]) == jobs, "Imported view has wrong job count")
        verify_encoding(row, catalog, factories)
        if row["family"] >= 0:
            fa = by_job(row, "FA")
            require(row["family"] not in fixed or fixed[row["family"]] == fa, "Fixed-family source FA mismatch")
            fixed[row["family"]] = fa
    return catalog

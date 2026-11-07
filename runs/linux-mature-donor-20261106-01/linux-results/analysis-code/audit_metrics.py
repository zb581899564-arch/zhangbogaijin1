"""All endpoint HVs checked with accepted Python HV on a different axis order."""
from statistics import median
import math
import numpy as np

from research.pilot_evaluation import hypervolume, igd, igd_plus
from analysis_common import COMPARISONS, REFERENCES, capture_folder, read_json, require, run_folder
from audit_replay import sorted_points


def independent_nd(raw):
    points = np.unique(np.asarray(raw, dtype=float).reshape(-1, 3), axis=0)
    require(np.isfinite(points).all(), "Nonfinite archive")
    survivors = []
    for point in points:
        if not survivors or not np.any(np.all(np.asarray(survivors) <= point, axis=1)):
            survivors.append(point)
    return np.asarray(survivors).reshape(-1, 3)


def close(actual, expected, label):
    require(math.isfinite(actual) and math.isfinite(expected)
            and math.isclose(actual, expected, abs_tol=2e-11, rel_tol=2e-11), f"Metric mismatch: {label}")


def endpoint_metrics(front, reference, norm):
    import moocore
    normal = (front - norm["lower"]) / norm["scale"]
    ref = (reference - norm["lower"]) / norm["scale"]
    values, errors = {}, {}
    for radius in REFERENCES:
        points = normal[np.all(normal < radius, axis=1)]
        accelerated = float(moocore.hypervolume(points, ref=[radius] * 3)) if len(points) else 0.0
        independent = hypervolume(normal[:, [2, 0, 1]], [radius] * 3)
        close(accelerated, independent, "moocore vs accepted pure Python HV, axis order [2,0,1]")
        values[str(radius)], errors[str(radius)] = independent, abs(accelerated - independent)
    return dict(front=front.tolist(), frontSize=len(front), HV=values,
                IGDplus=igd_plus(normal, ref), IGD=igd(normal, ref),
                objectiveMinimum=front.min(axis=0).tolist()), errors


def verify_metrics_record(record, expected):
    require(sorted_points(record["front"]) == sorted_points(expected["front"]), "Reported endpoint objectives differ")
    require(record["frontSize"] == expected["frontSize"], "Reported front count differs")
    require(record["objectiveMinimum"] == expected["objectiveMinimum"], "Reported objective minima differ")
    for radius in map(str, REFERENCES):
        close(record["HV"][radius], expected["HV"][radius], "reported HV")
    for name in ("IGDplus", "IGD"):
        close(record[name], expected[name], f"reported {name}")


def raw_coverage(a, b):
    aa, bb = np.asarray(a), np.asarray(b)
    covered_b = sum(bool(np.any(np.all(aa <= point, axis=1))) for point in bb)
    covered_a = sum(bool(np.any(np.all(bb <= point, axis=1))) for point in aa)
    return dict(C_A_B=covered_b / len(bb), C_B_A=covered_a / len(aa), coveredB=covered_b,
                coveredA=covered_a, totalB=len(bb), totalA=len(aa),
                sharedObjectiveVectors=len(set(map(tuple, aa)) & set(map(tuple, bb))))


def symmetric_improvement(a, b):
    if max(a, b) == 0:
        return 0.0
    scale = max(a, b)
    a, b = a / scale, b / scale
    return 200.0 * (b - a) / (a + b)


def check_distribution(record, values):
    close(record["median"], float(median(values)), "paired median")
    for actual, expected in zip(record["range"], (min(values), max(values))):
        close(actual, expected, "paired range")
    require(record["wins"] == sum(v > 0 for v in values)
            and record["ties"] == sum(v == 0 for v in values)
            and record["losses"] == sum(v < 0 for v in values)
            and record["tieTolerance"] == 0.0, "Paired descriptive signs differ")


def verify_pair(record, a, b):
    require(record["coverage"] == raw_coverage(a["front"], b["front"]), "Raw C counts or denominators differ")
    for radius in map(str, REFERENCES):
        delta = a["HV"][radius] - b["HV"][radius]
        close(record["HVAbsoluteDifference"][radius], delta, "paired HV difference")
        if b["HV"][radius] == 0:
            require(record["HVEffectPct"][radius] is None, "Undefined relative HV should be null")
        else:
            close(record["HVEffectPct"][radius], 100 * delta / b["HV"][radius], "paired relative HV")
    close(record["IGDplusSymmetricImprovementPct"], symmetric_improvement(a["IGDplus"], b["IGDplus"]), "symmetric IGD+")
    close(record["IGDplusImprovement"], b["IGDplus"] - a["IGDplus"], "IGD+ improvement")
    close(record["IGDImprovement"], b["IGD"] - a["IGD"], "IGD improvement")
    close(record["Cdelta"], record["coverage"]["C_A_B"] - record["coverage"]["C_B_A"], "C asymmetry")


def verify_comparisons(case, values, seeds):
    expected = {(a, b, endpoint) for a, b in COMPARISONS for endpoint in ("finalArchive", "workingPopulation")}
    observed = {(c["candidate"], c["control"], c["endpoint"]) for c in case["comparisons"]}
    require(observed == expected and len(case["comparisons"]) == len(expected), "Comparison registry differs")
    for row in case["comparisons"]:
        require([p["seed"] for p in row["pairs"]] == seeds, "Paired source seed order differs")
        for item in row["pairs"]:
            verify_pair(item, values[item["seed"], row["candidate"], row["endpoint"]],
                        values[item["seed"], row["control"], row["endpoint"]])
        for radius in map(str, REFERENCES):
            percents = [p["HVEffectPct"][radius] for p in row["pairs"]]
            if None not in percents:
                check_distribution(row["HVEffectPct"][radius], percents)
            else:
                require(row["HVEffectPct"][radius]["available"] is False, "Undefined HV summary was reported")
            check_distribution(row["HVAbsoluteDifference"][radius], [p["HVAbsoluteDifference"][radius] for p in row["pairs"]])
        for name in ("IGDplusSymmetricImprovementPct", "IGDplusImprovement", "IGDImprovement", "Cdelta"):
            check_distribution(row[name], [p[name] for p in row["pairs"]])


def verify_gains(record, final, background, receipt):
    require(record["successfulFE"] == receipt["successful"]
            and record["searchSeconds"] == receipt["searchSeconds"]
            and record["prepareSeconds"] == receipt.get("prepareSeconds", 0.0), "Reported costs differ from receipt")
    for radius in map(str, REFERENCES):
        gain = final["HV"][radius] - background["HV"][radius]
        close(record["gain"]["HVAboveA0"][radius], gain, "A0 HV increment")
        close(record["gain"]["HVAboveA0PerNewFE"][radius], gain / receipt["successful"], "HV/new FE")
        close(record["gain"]["HVAboveA0PerSearchSecond"][radius], gain / receipt["searchSeconds"], "HV/search second")


def audit_instance_metrics(root, spec, plan, reported=None):
    stem, norm = spec["stem"], spec["normalization"]
    fronts = {(seed, arm): independent_nd(read_json(run_folder(root, stem, seed, arm) / "front.json"))
              for seed in plan["seeds"] for arm in plan["arms"]}
    reference = independent_nd(np.vstack(list(fronts.values())))
    if reported is not None:
        require(reported["normalization"] == norm, "Normalization was changed")
        require(sorted_points(reported["reference"]) == sorted_points(reference), "Final empirical reference differs")
    values, checks = {}, []
    records = {(r["seed"], r["arm"]): r for r in reported["observations"]} if reported else {}
    if reported:
        require(set(records) == set(fronts) and len(reported["observations"]) == len(fronts), "Missing or duplicate observations")
    for seed in plan["seeds"]:
        background = independent_nd(read_json(capture_folder(root, stem, seed) / "background.json"))
        background_metrics, background_error = endpoint_metrics(background, reference, norm)
        checks.append(dict(seed=seed, arm="COMMON", endpoint="A0", absoluteHVErrors=background_error))
        for arm in plan["arms"]:
            folder = run_folder(root, stem, seed, arm)
            work = independent_nd([r["objectives"] for r in read_json(folder / "after.json")])
            for endpoint, front in (("finalArchive", fronts[seed, arm]), ("workingPopulation", work)):
                metrics, errors = endpoint_metrics(front, reference, norm)
                values[seed, arm, endpoint] = metrics
                checks.append(dict(seed=seed, arm=arm, endpoint=endpoint, absoluteHVErrors=errors))
                if reported:
                    verify_metrics_record(records[seed, arm][endpoint], metrics)
            if reported:
                verify_metrics_record(records[seed, arm]["A0"], background_metrics)
                verify_gains(records[seed, arm], values[seed, arm, "finalArchive"], background_metrics,
                             read_json(folder / "receipt.json"))
    if reported:
        verify_comparisons(reported, values, plan["seeds"])
    return dict(instance=stem, referenceSize=len(reference), endpoints=checks,
                acceptedPythonHVDifferentAxisOrder=[2, 0, 1], allEndpointHVsVerified=True,
                analysisReportVerified=reported is not None)

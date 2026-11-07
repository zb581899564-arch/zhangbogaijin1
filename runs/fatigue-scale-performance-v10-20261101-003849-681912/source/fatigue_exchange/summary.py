"""Descriptive effects with instance-level pairing, no seed pseudo-replication."""
from collections import defaultdict
import json
import numpy as np
from .protocol import PROTOCOL
from .records import read


def groups(rows, keys):
    result = defaultdict(list)
    for row in rows:
        result[tuple(row[k] for k in keys)].append(row)
    return result


def search_summary(rows):
    keys = ("split", "jobs", "model", "stratum", "mode", "seconds", "method")
    result = []
    for key, values in groups(rows, keys).items():
        result.append(dict(zip(keys, key)) | {"runs": len(values),
            "mean_gain_pct": float(np.mean([r["gain"]*100 for r in values])),
            "median_gain_pct": float(np.median([r["gain"]*100 for r in values])),
            "mean_full_FE": float(np.mean([r["full_decodes"] for r in values])),
            "mean_partial_calls": float(np.mean([r["partial_calls"] for r in values])),
            "mean_ms": float(np.mean([r["elapsed_ns"]/1e6 for r in values])),
            "max_overrun_ms": max(r["overrun_ns"]/1e6 for r in values),
            "positive_runs": sum(r["gain"] > 1e-10 for r in values)})
    return result


def comparisons(rows):
    result = []
    dimensions = ("split", "jobs", "model", "mode", "seconds")
    for key, block in groups(rows, dimensions).items():
        for stratum in ("barrier", "uniform", "combined"):
            selected = block if stratum == "combined" else [r for r in block if r["stratum"] == stratum]
            if not selected:
                continue
            means = {k: float(np.mean([r["gain"]*100 for r in values]))
                     for k, values in groups(selected, ("instance_seed", "method")).items()}
            seeds = sorted({r["instance_seed"] for r in selected})
            for a, b in PROTOCOL["comparisons"]:
                differences = [means[s, a]-means[s, b] for s in seeds]
                result.append(dict(zip(dimensions, key)) | {"stratum": stratum, "a": a, "b": b,
                    "instances": len(seeds), "mean_difference_pp": float(np.mean(differences)),
                    "wins": sum(d > 1e-8 for d in differences), "ties": sum(abs(d) <= 1e-8 for d in differences),
                    "losses": sum(d < -1e-8 for d in differences),
                    "instance_differences_pp": dict(zip(map(str, seeds), differences))})
    return result


def coverage_summary(rows):
    keys = ("split", "jobs", "model", "method")
    result = []
    for key, values in groups([r for r in rows if r["parent_strict"]], keys).items():
        result.append(dict(zip(keys, key)) | {"strict_parents": len(values),
            "covered_parents": sum(r["can_improve"] for r in values),
            "mean_improving_N2_coverage": float(np.mean([r["improving_N2_coverage"] for r in values])),
            "mean_p16": float(np.mean([r["p16"] for r in values])),
            "mean_unique_endpoints": float(np.mean([r["unique_endpoints"] for r in values]))})
    return result


def snapshot_summary(rows):
    expanded = [{**{k: r[k] for k in ("split", "jobs", "model", "stratum")}, "method": method,
                 **record} for r in rows for method, record in r["methods"].items()]
    keys = ("split", "jobs", "model", "stratum", "method")
    return [dict(zip(keys, key)) | {"pools": len(values),
        "mean_selected_gain_pct": float(np.mean([r["selected_gain"]*100 for r in values])),
        "mean_oracle_regret_pp": float(np.mean([r["oracle_regret"]*100 for r in values]))}
        for key, values in groups(expanded, keys).items()]


def summarize(output):
    searches = [{k: v for k, v in row.items() if k != "steps"} for row in read(output, "search")]
    return {"completion": json.loads((output/"completion.json").read_text(encoding="utf-8")),
        "search": search_summary(searches), "comparisons": comparisons(searches),
        "coverage": coverage_summary(list(read(output, "coverage"))),
        "snapshots": snapshot_summary(list(read(output, "snapshots")))}

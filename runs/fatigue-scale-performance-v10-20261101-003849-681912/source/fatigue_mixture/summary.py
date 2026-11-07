"""Instance-paired effects and descriptive use of each ordinary operator."""
import json
import numpy as np
from research.fatigue_exchange.summary import groups, search_summary
from .records import read
from .protocol import PROTOCOL


def compact(row):
    result = {k: v for k, v in row.items() if k != "steps"}
    accepted = [s for s in row["steps"] if s["accepted"]]
    result["plain_attempts"] = sum(s["family"] == "plain" for s in row["steps"])
    result["swap_attempts"] = len(row["steps"])-result["plain_attempts"]
    result["both_accepted"] = len({s["family"] for s in accepted}) == 2
    result["accepted_load_changes"] = sum(s["load_counts_changed"] for s in accepted)
    changed = False
    result["load_then_swap"] = False
    for step in accepted:
        if step["family"] == "swap_rebind" and changed:
            result["load_then_swap"] = True
        changed |= step["load_counts_changed"]
    return result


def comparisons(rows):
    dimensions = ("split", "jobs", "model", "stratum", "mode", "seconds")
    result = []
    for key, block in groups(rows, dimensions).items():
        means = {k: float(np.mean([r["gain"]*100 for r in values]))
                 for k, values in groups(block, ("instance_seed", "method")).items()}
        seeds = sorted({r["instance_seed"] for r in block})
        for a, b in PROTOCOL["comparisons"]:
            delta = [means[s, a]-means[s, b] for s in seeds]
            result.append(dict(zip(dimensions, key)) | {"a": a, "b": b, "instances": len(seeds),
                "mean_difference_pp": float(np.mean(delta)), "wins": sum(d > 1e-8 for d in delta),
                "ties": sum(abs(d) <= 1e-8 for d in delta), "losses": sum(d < -1e-8 for d in delta),
                "instance_differences_pp": dict(zip(map(str, seeds), delta))})
    return result


def summarize(output):
    rows = [compact(r) for r in read(output, "search")]
    summaries = search_summary(rows)
    keys = ("split", "jobs", "model", "stratum", "mode", "seconds", "method")
    by_key = groups(rows, keys)
    for record in summaries:
        values = by_key[tuple(record[k] for k in keys)]
        record.update({"mean_plain_attempts": float(np.mean([r["plain_attempts"] for r in values])),
            "mean_swap_attempts": float(np.mean([r["swap_attempts"] for r in values])),
            "both_families_accepted_runs": sum(r["both_accepted"] for r in values),
            "load_then_swap_runs": sum(r["load_then_swap"] for r in values),
            "mean_accepted_load_changes": float(np.mean([r["accepted_load_changes"] for r in values])),
            "actual_strict_parents": len({(r["instance_seed"], r["parent"]) for r in values if r["parent_strict"]})})
    cover = []
    for key, values in groups([r for r in read(output, "coverage") if r["parent_strict"]], ("split", "model", "method")).items():
        cover.append(dict(zip(("split", "model", "method"), key)) | {"strict_parents": len(values),
            "covered_parents": sum(r["can_improve"] for r in values),
            "mean_N2_improvement_coverage": float(np.mean([r["improving_N2_coverage"] for r in values])),
            "mean_p16": float(np.mean([r["p16"] for r in values])), "mean_p32": float(np.mean([r["p32"] for r in values]))})
    return {"completion": json.loads((output/"completion.json").read_text(encoding="utf-8")),
            "search": summaries, "comparisons": comparisons(rows), "coverage": cover}

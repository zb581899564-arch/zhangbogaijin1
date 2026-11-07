"""Same-campaign paired comparisons and a single globally selected classical method."""
import math
from statistics import median

from research.expansion_screen._metrics import compare, igd_guard_metrics, mean
from research.semantic_repair.metrics import _uncertainty


def select_classic(index, protocol, instances, seeds):
    baseline, scores = protocol["baseline"], []
    for label in protocol["external_comparators"]:
        ratios = []
        for instance in instances:
            a = mean(index[instance, seed, label]["hv"]["1.5"] for seed in seeds)
            b = mean(index[instance, seed, baseline]["hv"]["1.5"] for seed in seeds)
            ratio = a / b if b > 1e-12 else None
            ratios.append({"instance": instance, "external_mean_hv": a, "baseline_mean_hv": b,
                "ratio": ratio if ratio is not None and math.isfinite(ratio) else None})
        values = [row["ratio"] for row in ratios]
        resolved = all(value is not None for value in values)
        scores.append({"label": label, "instance_ratios": ratios, "resolved": resolved,
            "mean_ratio": mean(values) if resolved else None, "median_ratio": median(values) if resolved else None})
    selected = None
    if all(score["resolved"] for score in scores):
        best = max(score["mean_ratio"] for score in scores)
        tied = [score for score in scores if best - score["mean_ratio"] <= 1e-12]
        selected = min(tied, key=lambda score: (-score["median_ratio"], score["label"]))["label"]
    return {"selected": selected, "scores": scores, "resolved": selected is not None,
        "baseline": baseline, "reference": "1.5", "global_single_method": True,
        "scope": "Development selection; no instance-wise oracle or unbiased confirmatory claim"}


def comparison(index, protocol, candidate, control):
    args = (index, candidate, control, [row["stem"] for row in protocol["instances"]], protocol["algorithm_seeds"])
    final = {str(point): compare(*args, str(point)) for point in (1.25, 1.5, 2.)}
    return {"T": final, "uncertainty": _uncertainty(final["1.5"]),
        "halfTime": compare(*args, field="hv_half"),
        "FE15000": {"allInstances": compare(*args, field="hv_fe15000"),
            "completePairsOnly": compare(*args, field="hv_fe15000", available_only=True)},
        "IGDplus": igd_guard_metrics(*args)}


def comparisons(records, protocol):
    index = {(r["instance"], r["seed"], r["variant"]): r for r in records}
    if len(index) != protocol["runs"] or len(records) != len(index):
        raise ValueError("Complete unique campaign metrics required before interpretation")
    instances, seeds = [row["stem"] for row in protocol["instances"]], protocol["algorithm_seeds"]
    classic = select_classic(index, protocol, instances, seeds)
    candidate, baseline = protocol["candidate"], protocol["baseline"]
    pairs = [(candidate, control) for control in protocol["variants"] if control != candidate]
    pairs += [(baseline, control) for control in protocol["external_comparators"]]
    pairs += [tuple(pair) for pair in protocol.get("additional_pairs", [])]
    pairs = list(dict.fromkeys(pairs))
    effects = {a + "__vs__" + b: comparison(index, protocol, a, b) for a, b in pairs}
    return effects, classic

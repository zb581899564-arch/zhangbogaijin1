"""Instance-level means and paired directions, without epsilon denominators."""

import math
from statistics import median

DENOMINATOR_FLOOR = 1e-12


def mean(values):
    values = list(values)
    if not values:
        return None
    try:
        return math.fsum(values) / len(values)
    except OverflowError:
        return math.fsum(value / len(values) for value in values)


def effect(candidate, comparator):
    if comparator <= DENOMINATOR_FLOOR:
        return None
    # Algebraically the registered ratio-minus-one formula; subtract first to
    # avoid cancellation at the exact +/-1, -5 and -10 percent boundaries.
    value = 100 * ((candidate - comparator) / comparator)
    return value if math.isfinite(value) else None


def _value(record, field, reference):
    return record["hv"][reference] if field == "hv" else record.get(field)


def _instance_effect(index, candidate, comparator, instance, seeds, reference, field, win_seeds):
    pairs = [{"seed": seed, "candidate_hv": _value(index[instance, seed, candidate], field, reference),
              "comparator_hv": _value(index[instance, seed, comparator], field, reference)}
             for seed in seeds] if comparator is not None else []
    available = bool(pairs) and all(pair["candidate_hv"] is not None
                                    and pair["comparator_hv"] is not None for pair in pairs)
    for pair in pairs:
        a, b = pair["candidate_hv"], pair["comparator_hv"]
        pair["difference"] = a - b if a is not None and b is not None else None
    a = mean(pair["candidate_hv"] for pair in pairs) if available else None
    b = mean(pair["comparator_hv"] for pair in pairs) if available else None
    gain = effect(a, b) if available else None
    positives = sum(pair["difference"] > 0 for pair in pairs if pair["difference"] is not None)
    negatives = sum(pair["difference"] < 0 for pair in pairs if pair["difference"] is not None)
    reason = ("locked_external_unresolved" if comparator is None else "censored_checkpoint"
              if not available else "comparator_mean_HV_at_or_below_1e-12_or_nonfinite_ratio"
              if gain is None else None)
    return {"instance": instance, "available": available, "candidate_mean_hv": a,
            "comparator_mean_hv": b, "raw_mean_difference": a - b if available else None,
            "effect_percent": gain, "positive_seed_count": positives, "negative_seed_count": negatives,
            "practical_win": gain is not None and gain >= 1 and positives >= win_seeds,
            "practical_loss": gain is not None and gain <= -1 and negatives >= win_seeds,
            "paired_seeds": pairs, "unresolved_reason": reason}


def compare(index, candidate, comparator, instances, seeds, reference="1.5", field="hv",
            win_seeds=3, available_only=False):
    rows = [_instance_effect(index, candidate, comparator, instance, seeds, reference, field, win_seeds)
            for instance in instances]
    included = [row for row in rows if row["available"]] if available_only else rows
    resolved = bool(included) and all(row["effect_percent"] is not None for row in included)
    gains = [row["effect_percent"] for row in included] if resolved else []
    best = max(gains) if gains else None
    without_best = list(gains)
    if without_best:
        without_best.remove(best)
    return {"candidate": candidate, "comparator": comparator, "reference": reference, "field": field,
            "instances": rows, "resolved": resolved,
            "complete_pair_instances": sum(row["available"] for row in rows),
            "resolved_instances": sum(row["effect_percent"] is not None for row in rows),
            "mean_effect_percent": mean(gains), "median_effect_percent": median(gains) if gains else None,
            "mean_after_removing_best_instance_percent": mean(without_best),
            "best_effect_percent": best, "worst_effect_percent": min(gains) if gains else None,
            "removed_best_instance": max(included, key=lambda row: row["effect_percent"])["instance"] if gains else None,
            "worst_instance": min(included, key=lambda row: row["effect_percent"])["instance"] if gains else None,
            "practical_wins": sum(row["practical_win"] for row in rows),
            "practical_losses": sum(row["practical_loss"] for row in rows),
            "instances_effect_at_least_minus1_percent": sum(
                row["effect_percent"] is not None and row["effect_percent"] >= -1 for row in rows),
            "loss_greater_than5_percent_instances": sum(
                row["effect_percent"] is not None and row["effect_percent"] < -5 for row in rows),
            "loss_greater_than10_percent_instances": sum(
                row["effect_percent"] is not None and row["effect_percent"] < -10 for row in rows)}


def igd_guard_metrics(index, candidate, comparator, instances, seeds):
    rows = []
    for instance in instances:
        a = mean(index[instance, seed, candidate]["igdplus"] for seed in seeds)
        b = mean(index[instance, seed, comparator]["igdplus"] for seed in seeds) if comparator else None
        if b is None:
            worsening = None
        elif a == b == 0:
            worsening = 0.0
        elif math.isfinite(a + b):
            worsening = 200 * ((a - b) / (a + b))
        else:
            scale = max(a, b)
            worsening = 200 * ((a / scale) - (b / scale)) / ((a / scale) + (b / scale))
        rows.append({"instance": instance, "candidate_mean_igdplus": a,
                     "comparator_mean_igdplus": b, "symmetric_worsening_percent": worsening})
    values = [row["symmetric_worsening_percent"] for row in rows]
    resolved = all(value is not None for value in values)
    return {"instances": rows, "resolved": resolved,
            "median_symmetric_worsening_percent": median(values) if resolved else None,
            "instances_symmetric_worsening_greater_than5_percent": sum(
                value is not None and value > 5 for value in values)}


def select_external(index, config, instances, seeds):
    scores = []
    for label in config["external_comparators"]:
        ratios = []
        for instance in instances:
            a = mean(index[instance, seed, label]["hv"]["1.5"] for seed in seeds)
            b = mean(index[instance, seed, "BASELINE"]["hv"]["1.5"] for seed in seeds)
            ratio = a / b if b > DENOMINATOR_FLOOR else None
            ratios.append({"instance": instance, "external_mean_hv": a, "baseline_mean_hv": b,
                           "ratio": ratio if ratio is not None and math.isfinite(ratio) else None})
        values = [row["ratio"] for row in ratios]
        resolved = all(value is not None for value in values)
        scores.append({"label": label, "instance_ratios": ratios, "resolved": resolved,
                       "mean_ratio": mean(values) if resolved else None,
                       "median_ratio": median(values) if resolved else None})
    selected = None
    if scores and all(score["resolved"] for score in scores):
        maximum = max(score["mean_ratio"] for score in scores)
        tied = [score for score in scores if maximum - score["mean_ratio"] <= 1e-12]
        selected = min(tied, key=lambda score: (-score["median_ratio"], score["label"]))["label"]
    return {"selected": selected, "scores": scores, "resolved": selected is not None,
            "selection_reference": "1.5", "global_single_method": True,
            "scope": "Development-screen selection; not an unbiased confirmatory comparison"}

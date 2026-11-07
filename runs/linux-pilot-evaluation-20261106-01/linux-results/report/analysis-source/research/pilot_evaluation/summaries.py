"""Descriptive paired effects without pooling seeds as independent instances."""
from collections import defaultdict
from statistics import median

from .validation import finite, label


def igd_plus_symmetric_effect(candidate, control):
    """2*(control-candidate)/(|control|+|candidate|), positive favors candidate.

    Both zero maps to zero. This is a ratio in [-2, 2], not a percent;
    multiplying by 100 yields the symmetric percentage representation.
    """
    candidate, control = finite(candidate, "candidate"), finite(control, "control")
    if min(candidate, control) < 0:
        raise ValueError("IGD+ cannot be negative")
    magnitude = max(candidate, control)
    if magnitude == 0:
        return 0.0
    a, b = candidate / magnitude, control / magnitude
    return 2 * (b - a) / (abs(b) + abs(a))


def _distribution(values):
    return {"median": float(median(values)), "range": [min(values), max(values)]}


def _directions(values, tolerance):
    wins = sum(value > tolerance for value in values)
    losses = sum(value < -tolerance for value in values)
    return {"wins": wins, "ties": len(values) - wins - losses, "losses": losses}


def _instance_summary(rows, metric, tolerance):
    result = {"seed_count": len(rows), "raw": rows,
              "candidate": _distribution([row["candidate"] for row in rows]),
              "control": _distribution([row["control"] for row in rows]),
              "paired_improvement": _distribution([row["improvement"] for row in rows]),
              "seed_directions": _directions([row["improvement"] for row in rows], tolerance)}
    if metric == "IGDplus":
        result["symmetric_effect"] = _distribution([row["symmetric_effect"] for row in rows])
    return result


def paired_summary(rows, *, metric, higher_is_better, tie_tolerance=0.0):
    """Rows: instance, seed, candidate (number), control (number).

    Summarizes each instance's paired seeds, then the equally weighted instance
    median improvements. No p-values, confidence claims or protocol gates.
    """
    label(metric, "metric")
    if type(higher_is_better) is not bool:
        raise ValueError("higher_is_better must be boolean")
    if metric in ("IGD", "IGDplus") and higher_is_better:
        raise ValueError("IGD and IGD+ are minimized")
    if metric == "HV" and not higher_is_better:
        raise ValueError("HV is maximized")
    tolerance = finite(tie_tolerance, "tie_tolerance")
    if tolerance < 0:
        raise ValueError("tie_tolerance must be nonnegative and fixed before analysis")
    grouped, seen = defaultdict(list), set()
    for row in rows:
        instance = label(row["instance"], "instance")
        seed = row["seed"]
        if isinstance(seed, bool) or not isinstance(seed, (str, int)) or not str(seed):
            raise ValueError("seed must be an integer or nonempty string")
        key = (instance, str(seed))
        if key in seen:
            raise ValueError(f"Duplicate instance/seed pair: {key}")
        seen.add(key)
        candidate, control = finite(row["candidate"], "candidate"), finite(row["control"], "control")
        if metric in ("IGD", "IGDplus", "HV") and min(candidate, control) < 0:
            raise ValueError(f"{metric} cannot be negative")
        difference = candidate - control
        raw = {"instance": instance, "seed": seed, "candidate": candidate, "control": control,
               "candidate_minus_control": difference,
               "improvement": difference if higher_is_better else -difference}
        if metric == "IGDplus":
            raw["symmetric_effect"] = igd_plus_symmetric_effect(candidate, control)
        grouped[instance].append(raw)
    if not grouped:
        raise ValueError("At least one complete paired row is required")
    instances = {name: _instance_summary(group, metric, tolerance) for name, group in grouped.items()}
    medians = [item["paired_improvement"]["median"] for item in instances.values()]
    result = {"metric": metric, "higher_is_better": higher_is_better,
              "tie_tolerance": tolerance, "instance_count": len(instances),
              "by_instance": instances, "instance_median_improvement": _distribution(medians),
              "instance_directions": _directions(medians, tolerance),
              "interpretation": "Descriptive paired signs; seeds are within-instance repeats"}
    if metric == "IGDplus":
        result["instance_median_symmetric_effect"] = _distribution(
            [item["symmetric_effect"]["median"] for item in instances.values()])
    return result

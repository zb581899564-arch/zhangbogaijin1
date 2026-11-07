"""Paired instance summaries, factorial interactions, and descriptive uncertainty."""
from statistics import median
import numpy as np

# These helpers contain no historical verdict or comparator selection logic.
from research.expansion_screen._metrics import compare, effect, igd_guard_metrics, mean

PAIRS = (
    ("S_ONLY", "V2", "S_at_O_off"),
    ("O_ONLY", "V2", "O_at_S_off"),
    ("SO", "V2", "combined_repair"),
    ("SO", "O_ONLY", "S_at_O_on"),
    ("SO", "S_ONLY", "O_at_S_on"),
    ("SO", "NSGA2_CONTROL", "repaired_baseline_vs_locked_NSGA"),
    ("SYNC_FIX", "NSGA2_CONTROL", "sync_vs_locked_NSGA"),
    ("SHARE_FIX", "NSGA2_CONTROL", "share_vs_locked_NSGA"),
    ("SYNC_FIX", "SO", "organization_cost"),
    ("SHARE_FIX", "SYNC_FIX", "sharing_increment"),
    ("SHARE_FIX", "SO", "net_sharing_gain"),
)


def _uncertainty(comparison):
    values = [row["effect_percent"] for row in comparison["instances"]]
    if not values or any(value is None for value in values):
        return {"status": "UNRESOLVED"}
    points = np.asarray(values)
    # Resample instances, never 30 correlated seed runs as independent problems.
    rng = np.random.default_rng(20261102)
    samples = rng.choice(points, size=(4000, len(points)), replace=True).mean(axis=1)
    return {"status": "EXPLORATORY", "units": "six development instances; seed repeats aggregated within each",
            "bootstrap_seed": 20261102, "bootstrap_replicates": 4000,
            "mean_effect_percent_interval95": np.quantile(samples, [.025, .975]).tolist(),
            "leave_one_instance_out_mean_percent": [float(np.delete(points, i).mean()) for i in range(len(points))],
            "scope": "Descriptive uncertainty; small selected development sample, no p-value gate or generalization claim"}


def interaction(index, instances, seeds, reference="1.5", field="hv"):
    def value(instance, seed, label):
        record = index[instance, seed, label]
        return record["hv"][reference] if field == "hv" else record[field]

    rows = []
    for instance in instances:
        pairs = []
        for seed in seeds:
            values = {label: value(instance, seed, label) for label in ("V2", "S_ONLY", "O_ONLY", "SO")}
            available = all(item is not None for item in values.values())
            raw = values["SO"] - values["S_ONLY"] - values["O_ONLY"] + values["V2"] if available else None
            percentage = 100 * raw / values["V2"] if available and values["V2"] > 1e-12 else None
            pairs.append({"seed": seed, **values, "interaction_hv": raw,
                          "interaction_percent_of_paired_V2": percentage})
        available = all(pair["interaction_hv"] is not None for pair in pairs)
        raw_mean = mean(pair["interaction_hv"] for pair in pairs) if available else None
        v2_mean = mean(pair["V2"] for pair in pairs) if available else None
        normalized = 100 * raw_mean / v2_mean if available and v2_mean > 1e-12 else None
        seed_percents = [pair["interaction_percent_of_paired_V2"] for pair in pairs]
        rows.append({"instance": instance, "available": available, "paired_seeds": pairs,
                     "mean_interaction_hv": raw_mean, "V2_mean_hv": v2_mean,
                     "interaction_percent_of_instance_mean_V2": normalized,
                     "mean_paired_seed_interaction_percent": mean(seed_percents)
                     if all(value is not None for value in seed_percents) else None})
    values = [row["interaction_percent_of_instance_mean_V2"] for row in rows]
    resolved = all(value is not None for value in values)
    return {"reference": reference, "field": field, "instances": rows, "resolved": resolved,
            "formula": "HV_SO-HV_S_ONLY-HV_O_ONLY+HV_V2; every seed percentage uses its own V2 HV",
            "mean_interaction_percent": mean(values) if resolved else None,
            "median_interaction_percent": median(values) if resolved else None,
            "worst_interaction_percent": min(values) if resolved else None,
            "complete_instances": sum(row["available"] for row in rows)}


def comparisons(records, protocol):
    index = {(row["instance"], row["seed"], row["variant"]): row for row in records}
    if len(index) != len(records):
        raise ValueError("Duplicated metric cell")
    instances = [row["stem"] for row in protocol["instances"]]
    seeds = protocol["algorithm_seeds"]
    results = {}
    for candidate, control, purpose in PAIRS:
        final = {reference: compare(index, candidate, control, instances, seeds, reference)
                 for reference in ("1.25", "1.5", "2.0")}
        primary = final["1.5"]
        fe_all = compare(index, candidate, control, instances, seeds, field="hv_fe15000")
        fe_available = compare(index, candidate, control, instances, seeds,
                               field="hv_fe15000", available_only=True)
        results[candidate + "__vs__" + control] = {
            "purpose": purpose, "final": final, "uncertainty": _uncertainty(primary),
            "half_time": compare(index, candidate, control, instances, seeds, field="hv_half"),
            "FE15000": {"all_instances": fe_all, "complete_pairs_only": fe_available,
                        "scope": "Diagnostic conditional on both methods reaching FE15000 in all5 seeds of an instance; no imputation"},
            "igdplus": igd_guard_metrics(index, candidate, control, instances, seeds),
        }
    interactions = {reference: interaction(index, instances, seeds, reference)
                    for reference in ("1.25", "1.5", "2.0")}
    interactions["half_time"] = interaction(index, instances, seeds, field="hv_half")
    interactions["FE15000"] = interaction(index, instances, seeds, field="hv_fe15000")
    return {"comparisons": results, "factorial_interactions": interactions}

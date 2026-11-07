"""Same-campaign comparisons and specialization x sharing interaction."""
from research.expansion_screen._metrics import compare, igd_guard_metrics, mean
from research.semantic_repair.metrics import _uncertainty
from .protocol import PAIRS


def comparisons(records, protocol):
    index = {(row["instance"], row["seed"], row["variant"]): row for row in records}
    if len(index) != 150:
        raise ValueError("All150 unique metric cells required")
    effects = {}
    for candidate, control in PAIRS:
        args = index, candidate, control, [row["stem"] for row in protocol["instances"]], protocol["algorithm_seeds"]
        t = {str(point): compare(*args, str(point)) for point in (1.25, 1.5, 2.)}
        effects[candidate + "__vs__" + control] = {"T": t, "uncertainty": _uncertainty(t["1.5"]),
            "FE15000": {"allInstances": compare(*args, field="hv_fe15000"),
                "completePairsOnly": compare(*args, field="hv_fe15000", available_only=True)},
            "halfTime": compare(*args, field="hv_half"), "IGDplus": igd_guard_metrics(*args)}
    return effects, {field: interaction(index, protocol, field) for field in ("T", "FE15000", "halfTime")}


def interaction(index, protocol, field):
    instances = []
    labels = ("SHARE_SPECIAL", "SYNC_SPECIAL", "SHARE_UNIFORM", "SYNC_UNIFORM")
    for instance in protocol["instances"]:
        pairs = []
        for seed in protocol["algorithm_seeds"]:
            def value(label):
                row = index[instance["stem"], seed, label]
                return row["hv"]["1.5"] if field == "T" else row["hv_fe15000" if field == "FE15000" else "hv_half"]
            values = {label: value(label) for label in labels}
            raw = values[labels[0]] - values[labels[1]] - values[labels[2]] + values[labels[3]] if all(v is not None for v in values.values()) else None
            pairs.append({"seed": seed, "values": values, "rawInteractionHV": raw})
        available = all(pair["rawInteractionHV"] is not None for pair in pairs)
        denominator = mean(pair["values"]["SYNC_UNIFORM"] for pair in pairs) if available else None
        raw_mean = mean(pair["rawInteractionHV"] for pair in pairs) if available else None
        effect = 100 * raw_mean / denominator if denominator is not None and denominator > 1e-12 else None
        instances.append({"instance": instance["stem"], "available": available, "rawMeanInteractionHV": raw_mean,
            "SYNCUniformMeanHV": denominator, "interactionPercentOfSYNCUniform": effect, "pairs": pairs})
    effects = [row["interactionPercentOfSYNCUniform"] for row in instances]
    resolved = all(value is not None for value in effects)
    return {"field": field, "instances": instances, "resolved": resolved,
        "meanInteractionPercent": mean(effects) if resolved else None,
        "positiveInstances": sum(value > 0 for value in effects) if resolved else None}


def signal(effects, interactions):
    primary = effects["SHARE_SPECIAL__vs__SHARE_UNIFORM"]
    t = primary["T"]["1.5"]; fe = primary["FE15000"]["allInstances"]["mean_effect_percent"]
    interaction_mean = interactions["T"]["meanInteractionPercent"]
    flags = {"meanTAtLeast1Percent": t["mean_effect_percent"] is not None and t["mean_effect_percent"] >= 1.,
        "atLeast3PracticalInstanceWins": t["practical_wins"] >= 3,
        "meanFEPositive": fe is not None and fe > 0,
        "meanTInteractionPositive": interaction_mean is not None and interaction_mean > 0}
    return {"conditions": flags, "supportedDescriptiveSignal": all(flags.values()),
        "scope": "Entire target-specialization factor: grouping, teacher/pbest, Q reward and local preference; not only Q reward; no scale-up or publication qualification"}

"""Predeclared difference-in-differences, with the same instance/seed budget units."""
from statistics import median
from research.expansion_screen._metrics import mean


def _value(row, field):
    return row["hv"]["1.5"] if field == "T" else row["hv_half" if field == "halfTime" else "hv_fe15000"]


def interaction(records, protocol, spec, field):
    index = {(r["instance"], r["seed"], r["variant"]): r for r in records}
    labels = list(dict.fromkeys(spec["positive"] + spec["negative"] + [spec["normalizer"]]))
    rows = []
    for instance in protocol["instances"]:
        pairs = []
        for seed in protocol["algorithm_seeds"]:
            values = {label: _value(index[instance["stem"], seed, label], field) for label in labels}
            available = all(value is not None for value in values.values())
            raw = (sum(values[label] for label in spec["positive"]) - sum(values[label] for label in spec["negative"])) if available else None
            pairs.append({"seed": seed, "values": values, "rawInteractionHV": raw})
        available = all(pair["rawInteractionHV"] is not None for pair in pairs)
        raw_mean = mean(pair["rawInteractionHV"] for pair in pairs) if available else None
        denominator = mean(pair["values"][spec["normalizer"]] for pair in pairs) if available else None
        effect = 100 * raw_mean / denominator if denominator is not None and denominator > 1e-12 else None
        rows.append({"instance": instance["stem"], "available": available,
            "rawMeanInteractionHV": raw_mean, "normalizerMeanHV": denominator,
            "interactionPercent": effect, "paired_seeds": pairs})
    values = [row["interactionPercent"] for row in rows]
    resolved = all(value is not None for value in values)
    return {"name": spec["name"], "formula": spec, "field": field, "instances": rows,
        "resolved": resolved, "meanInteractionPercent": mean(values) if resolved else None,
        "medianInteractionPercent": median(values) if resolved else None,
        "positiveInstances": sum(value > 0 for value in values) if resolved else None,
        "scope": "Descriptive interaction on six development instances; separate from candidate admission"}


def interactions(records, protocol):
    return {spec["name"]: {field: interaction(records, protocol, spec, field)
        for field in ("T", "halfTime", "FE15000")} for spec in protocol.get("interactions", [])}

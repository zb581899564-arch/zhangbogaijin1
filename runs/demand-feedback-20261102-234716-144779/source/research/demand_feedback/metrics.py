"""Reuse registered metrics while comparing only this90-run campaign."""
from research.expansion_screen._metrics import compare, igd_guard_metrics
from research.semantic_repair.metrics import _uncertainty
from .protocol import PAIRS


def comparisons(records, protocol):
    index = {(row["instance"], row["seed"], row["variant"]): row for row in records}
    if len(index) != 90:
        raise ValueError("All90 unique contemporaneous metric owners required")
    effects = {}
    for candidate, control in PAIRS:
        args = index, candidate, control, [row["stem"] for row in protocol["instances"]], protocol["algorithm_seeds"]
        t = {str(point): compare(*args, str(point)) for point in (1.25, 1.5, 2.)}
        effects[candidate + "__vs__" + control] = {"T": t, "uncertainty": _uncertainty(t["1.5"]),
            "FE15000": {"allInstances": compare(*args, field="hv_fe15000"),
                "completePairsOnly": compare(*args, field="hv_fe15000", available_only=True)},
            "halfTime": compare(*args, field="hv_half"), "IGDplus": igd_guard_metrics(*args)}
    return effects


def signal(effects):
    direct = effects["SHARE_DEMAND_SPECIAL__vs__SHARE_SHAM_SPECIAL"]
    original = effects["SHARE_DEMAND_SPECIAL__vs__SHARE_SPECIAL"]["T"]["1.5"]
    t = direct["T"]["1.5"]; fe = direct["FE15000"]["allInstances"]["mean_effect_percent"]
    flags = {"DEMANDvsSHAMMeanTAtLeast1Percent": t["mean_effect_percent"] is not None and t["mean_effect_percent"] >= 1.,
        "DEMANDvsSHAMAtLeast3PracticalInstanceWins": t["practical_wins"] >= 3,
        "DEMANDvsSHAMMeanFEPositive": fe is not None and fe > 0,
        "DEMANDvsOriginalMeanTNonnegative": original["mean_effect_percent"] is not None and original["mean_effect_percent"] >= 0,
        "DEMANDvsOriginalMedianTNonnegative": original["median_effect_percent"] is not None and original["median_effect_percent"] >= 0}
    return {"conditions": flags, "supportedDescriptiveSignal": all(flags.values()),
        "scope": "Predeclared fixed rule once; no new cap/frequency/thresholds or RL; no formal scale-up/publication verdict",
        "NSGA": "Not run in step3; no historical wall-clock scores mixed into this campaign"}

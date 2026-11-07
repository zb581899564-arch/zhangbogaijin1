"""Prespecified paired descriptive signals, never a weighted winner score."""
from statistics import median

from research.pilot_evaluation import exact_coverage, igd_plus_symmetric_effect, paired_summary
from report_io import require_linux


def _distribution(values):
    known = [value for value in values if value is not None]
    return {"median": median(known) if known else None,
            "range": [min(known), max(known)] if known else None,
            "knownPairs": len(known), "unknownPairs": len(values) - len(known)}


def _relative(candidate, control, higher):
    if control <= 0:
        return None
    return 100 * (candidate / control - 1) * (1 if higher else -1)


def _paired_row(candidate, control, thresholds):
    coverage = exact_coverage(candidate["rawFront"], control["rawFront"])
    hv = _relative(candidate["HV"], control["HV"], True)
    igdp = 100 * igd_plus_symmetric_effect(candidate["IGDplus"], control["IGDplus"])
    c_delta = 100 * (coverage["C_A_B"] - coverage["C_B_A"])
    directions = [1 if value > 0 else -1 if value < 0 else 0 for value in (hv, igdp, c_delta) if value is not None]
    return {"instance": candidate["instance"], "seed": candidate["seed"],
            "candidate": candidate["arm"], "control": control["arm"],
            "candidateHV": candidate["HV"], "controlHV": control["HV"], "hvRelativeImprovementPercent": hv,
            "candidateIGDplus": candidate["IGDplus"], "controlIGDplus": control["IGDplus"],
            "igdPlusSymmetricImprovementPercent": igdp,
            "candidateIGD": candidate["IGD"], "controlIGD": control["IGD"],
            "igdRawImprovement": control["IGD"] - candidate["IGD"], **coverage,
            "coverageAdvantagePercentagePoints": c_delta,
            "costRelativeReductionPercent": _relative(candidate["searchSecondsInclusive"], control["searchSecondsInclusive"], False),
            "hvSignal": hv is not None and hv >= thresholds["hvSignalPercent"],
            "hvAdverseSignal": hv is not None and hv <= -thresholds["hvSignalPercent"],
            "igdPlusSignal": igdp >= thresholds["igdPlusSymmetricSignalPercent"],
            "igdPlusAdverseSignal": igdp <= -thresholds["igdPlusSymmetricSignalPercent"],
            "cReverseFlag": c_delta <= -thresholds["cReverseFlagPercentagePoints"],
            "metricDirectionsDisagree": min(directions) < 0 < max(directions),
            "hvSensitivityRelativeImprovementPercent": {
                key: _relative(value, control["hvSensitivity"][key], True)
                for key, value in candidate["hvSensitivity"].items()}}


def _instance_summary(instance, rows, thresholds):
    selected = [row for row in rows if row["instance"] == instance]
    result = {"instance": instance, "pairedSeeds": len(selected),
              "statistics": {key: _distribution([row[key] for row in selected]) for key in (
                  "hvRelativeImprovementPercent", "igdPlusSymmetricImprovementPercent", "igdRawImprovement",
                  "C_A_B", "C_B_A", "coverageAdvantagePercentagePoints", "costRelativeReductionPercent")},
              "signalSeedCounts": {key: sum(row[key] for row in selected) for key in (
                  "hvSignal", "hvAdverseSignal", "igdPlusSignal", "igdPlusAdverseSignal", "cReverseFlag", "metricDirectionsDisagree")}}
    for name, key in (("HV", "hvRelativeImprovementPercent"), ("IGDplus", "igdPlusSymmetricImprovementPercent"),
                      ("coverageAsymmetry", "coverageAdvantagePercentagePoints")):
        result[name + "PositiveSeedCount"] = sum(row[key] is not None and row[key] > 0 for row in selected)
        result[name + "NegativeSeedCount"] = sum(row[key] is not None and row[key] < 0 for row in selected)
        result[name + "AtLeastTwoPositiveSeeds"] = result[name + "PositiveSeedCount"] >= 2
    signs = [result["statistics"][key]["median"] for key in (
        "hvRelativeImprovementPercent", "igdPlusSymmetricImprovementPercent", "coverageAdvantagePercentagePoints")]
    known = [value for value in signs if value is not None]
    result["medianDirectionsDisagree"] = bool(known and min(known) < 0 < max(known))
    result["decision"] = "DESCRIPTIVE_SIGNALS_ONLY_NO_WINNER_OR_EXPANSION_DECISION"
    return result


def pairwise_comparisons(final_rows, plan):
    require_linux()
    index = {(row["instance"], row["seed"], row["arm"]): row for row in final_rows}
    result = []
    for candidate_name, control_name, primary in (("FULL", "GLOBAL_ONLY", True), ("FULL", "LOCAL_ONLY", True),
                                                 ("GLOBAL_ONLY", "LOCAL_ONLY", False)):
        rows, metric_rows = [], {name: [] for name in ("HV", "IGDplus", "IGD")}
        for spec in plan["instances"]:
            for seed in plan["seeds"]:
                candidate = index[(spec["stem"], seed, candidate_name)]
                control = index[(spec["stem"], seed, control_name)]
                rows.append(_paired_row(candidate, control, plan["thresholds"]))
                for metric in metric_rows:
                    metric_rows[metric].append({"instance": spec["stem"], "seed": seed,
                                                "candidate": candidate[metric], "control": control[metric]})
        result.append({"candidate": candidate_name, "control": control_name, "primary": primary,
                       "rawPairs": rows,
                       "byInstance": [_instance_summary(spec["stem"], rows, plan["thresholds"]) for spec in plan["instances"]],
                       "pairedMetricSummaries": {metric: paired_summary(values, metric=metric, higher_is_better=metric == "HV")
                                                 for metric, values in metric_rows.items()}})
    return {"comparisons": result, "thresholds": plan["thresholds"], "thresholdComparison": "inclusive >= or <=",
            "interpretation": "Positive effects favor candidate; C fractions have different denominators. No metric vote or significance test.",
            "sameTimeQualityClaim": False, "winner": None}

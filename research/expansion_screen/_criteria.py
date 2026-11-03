"""Readable threshold groups, all driven by the frozen JSON configuration."""

import operator

OPERATORS = {">=": operator.ge, "<=": operator.le, "==": operator.eq}


def condition(value, threshold, comparison, resolved=True):
    resolved = resolved and value is not None
    return {"value": value, "operator": comparison, "threshold": threshold,
            "resolved": resolved, "pass": bool(resolved and OPERATORS[comparison](value, threshold))}


def group(conditions):
    return {"conditions": conditions, "pass": all(item["pass"] for item in conditions.values())}


def _effect_group(metrics, thresholds):
    fields = {"mean_effect_min_percent": ("mean_effect_percent", ">="),
              "median_effect_min_percent": ("median_effect_percent", ">="),
              "mean_after_removing_best_instance_min_percent": (
                  "mean_after_removing_best_instance_percent", ">="),
              "practical_wins_min": ("practical_wins", ">="),
              "instances_effect_at_least_minus1_percent_min": (
                  "instances_effect_at_least_minus1_percent", ">="),
              "mean_effect_max_percent": ("mean_effect_percent", "<="),
              "median_effect_max_percent": ("median_effect_percent", "<="),
              "practical_losses_min": ("practical_losses", ">=")}
    return group({name: condition(metrics[field], threshold, comparison, metrics["resolved"])
                  for name, threshold in thresholds.items() for field, comparison in [fields[name]]})


def protective_groups(comparisons, igdplus, sensitivity, config):
    rules = config["green_all_required"]
    groups = {}
    for label in ("BASELINE", "strongest_external"):
        metrics = comparisons[label]
        thresholds = rules["tail_guard_each_BASELINE_and_strongest_external"]
        groups[f"tail_guard_{label}"] = group({
            "loss_greater_than5_percent_max_instances": condition(
                metrics["loss_greater_than5_percent_instances"],
                thresholds["loss_greater_than5_percent_max_instances"], "<=", metrics["resolved"]),
            "loss_greater_than10_percent_max_instances": condition(
                metrics["loss_greater_than10_percent_instances"],
                thresholds["loss_greater_than10_percent_max_instances"], "<=", metrics["resolved"])})
        metrics = igdplus[label]
        thresholds = rules["igdplus_guard_each_BASELINE_and_strongest_external"]
        groups[f"igdplus_guard_{label}"] = group({
            "median_symmetric_worsening_max_percent": condition(
                metrics["median_symmetric_worsening_percent"],
                thresholds["median_symmetric_worsening_max_percent"], "<=", metrics["resolved"]),
            "instances_symmetric_worsening_greater_than5_percent_max": condition(
                metrics["instances_symmetric_worsening_greater_than5_percent"],
                thresholds["instances_symmetric_worsening_greater_than5_percent_max"],
                "<=", metrics["resolved"])})
    thresholds = rules["each_sensitivity_reference"]
    for reference, refs in sensitivity.items():
        conditions = {}
        for label in ("BASELINE", "strongest_external"):
            for statistic in ("mean", "median"):
                name = f"versus_{label}_{statistic}_min_percent"
                metrics = refs[label]
                conditions[name] = condition(metrics[f"{statistic}_effect_percent"], thresholds[name],
                                             ">=", metrics["resolved"])
        groups[f"sensitivity_{reference}"] = group(conditions)
    return groups


def initial_green_groups(comparisons, igdplus, sensitivity, config):
    rules = config["green_all_required"]
    groups = {"validity_and_complete_270_runs": group({"valid_complete": condition(True, True, "==")})}
    for label in ("BASELINE", "TAIL", "strongest_external", "matched_parent"):
        groups[f"versus_{label}"] = _effect_group(comparisons[label], rules[f"versus_{label}"])
    groups.update(protective_groups(comparisons, igdplus, sensitivity, config))
    return groups


def initial_red_groups(comparisons, config):
    rules = config["red_any_sufficient_after_validity"]
    groups = {"strongest_external": _effect_group(comparisons["strongest_external"], rules["strongest_external"])}
    for label in ("BASELINE", "TAIL"):
        groups[f"versus_{label}"] = _effect_group(comparisons[label], rules["either_BASELINE_or_TAIL"])
    metrics = comparisons["strongest_external"]
    groups["large_losses_to_strongest_external"] = group({
        "loss_greater_than10_percent_min_instances": condition(
            metrics["loss_greater_than10_percent_instances"],
            rules["large_losses_to_strongest_external"]["loss_greater_than10_percent_min_instances"], ">=")})
    return groups


def followup_green_groups(comparisons, igdplus, sensitivity, original_parent_passed, config):
    rules = config["followup"]["bounded_continue_if_all"]
    groups = {}
    for label, prefix in (("BASELINE", "versus_BASELINE"), ("strongest_external", "versus_locked_external")):
        thresholds = {f"{statistic}_effect_min_percent": rules[f"{prefix}_{statistic}_min_percent"]
                      for statistic in ("mean", "median")}
        if label == "BASELINE":
            thresholds["practical_wins_min"] = rules["versus_BASELINE_practical_wins_min"]
        groups[prefix] = _effect_group(comparisons[label], thresholds)
    groups.update(protective_groups(comparisons, igdplus, sensitivity, config))
    groups["matched_parent_green_in_original_screen"] = group({"original_screen_condition": condition(
        original_parent_passed, rules["matched_parent_green_in_original_screen"], "==")})
    return groups

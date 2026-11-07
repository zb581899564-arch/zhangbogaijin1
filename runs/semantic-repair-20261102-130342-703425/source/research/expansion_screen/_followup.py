"""One candidate, one bounded followup, with the initial external locked."""

from collections.abc import Mapping
from copy import deepcopy
from statistics import median

from ._criteria import condition, group
from ._metrics import compare


def _eligibility(index, detail, external, config, instances, seeds):
    candidate = detail["candidate"]
    fe = compare(index, candidate, external, instances, seeds, field="hv_fe15000", available_only=True)
    half = compare(index, candidate, external, instances, seeds, field="hv_half")
    terminal = detail["comparisons"]["strongest_external"]
    changes = [{"instance": final["instance"], "terminal_effect_percent": final["effect_percent"],
                "half_effect_percent": early["effect_percent"],
                "increase_percentagepoints": final["effect_percent"] - early["effect_percent"]
                if final["effect_percent"] is not None and early["effect_percent"] is not None else None}
               for final, early in zip(terminal["instances"], half["instances"])]
    increases = [row["increase_percentagepoints"] for row in changes]
    late_median = median(increases) if all(value is not None for value in increases) else None
    # These numeric cutoffs are fixed in the JSON's eligible_if protocol text.
    fe_gate = group({"complete_instance_pairs": condition(fe["complete_pair_instances"], 4, ">="),
                     "median_FE15000_gain_percent": condition(fe["median_effect_percent"], 2.0, ">=", fe["resolved"])})
    late_gate = group({"median_terminal_minus_half_gain_percentagepoints": condition(late_median, 2.0, ">=")})
    conditions = {"no_red_condition": condition(not detail["triggered_red_conditions"], True, "=="),
                  "locked_external_resolved": condition(external is not None, True, "=="),
                  "matched_parent_initial_green": condition(
                      detail["green_conditions"]["versus_matched_parent"]["pass"], True, "=="),
                  "TAIL_initial_green": condition(
                      detail["green_conditions"]["versus_TAIL"]["pass"], True, "=="),
                  "quantified_cost_or_startup_question": condition(fe_gate["pass"] or late_gate["pass"], True, "==")}
    eligibility = group(conditions)
    return {"eligible": eligibility["pass"], "conditions": eligibility,
            "FE15000": {"comparison": fe, "gate": fe_gate},
            "late_catchup": {"half_comparison": half, "instance_changes": changes,
                             "median_increase_percentagepoints": late_median, "gate": late_gate}}


def followup_plan(index, candidates, external, config, instances, seeds):
    primary, secondary = config["primary_candidate"], config["secondary_candidate"]
    eligibility = {label: _eligibility(index, detail, external, config, instances, seeds)
                   for label, detail in candidates.items()}
    priority = None
    if candidates[primary]["color"] == "YELLOW":
        priority = primary
    elif candidates[primary]["color"] == "GREEN" and candidates[secondary]["color"] == "YELLOW":
        priority = secondary
    selected = priority if priority and eligibility[priority]["eligible"] else None
    return {"max_campaigns": config["followup"]["max_campaigns"], "campaigns_used": 0,
            "priority_candidate": priority, "eligibility": eligibility, "selected_candidate": selected,
            "locked_external": external, "variants": [selected, "BASELINE", external] if selected else [],
            "seeds": list(config["followup"]["seeds"]), "time_multiplier": 2,
            "locked_instances": list(instances),
            "locked_model": deepcopy(config["model"]),
            "locked_primary_reference": list(config["metrics"]["primary_reference"]),
            "locked_sensitivity_references": deepcopy(config["metrics"]["sensitivity_references"]),
            "expected_runs": config["followup"]["runs"] if selected else 0,
            "further_followup_allowed": selected is not None,
            "single_use_receipt_required": True,
            "scope": "One bounded campaign; no parameter changes or second extension"}


def locked_authorization(config, initial_result):
    try:
        return _locked_authorization(config, initial_result)
    except (KeyError, TypeError, ValueError) as error:
        return None, f"Malformed followup authorization: {error}"


def _locked_authorization(config, initial_result):
    if not isinstance(config, Mapping) or not isinstance(initial_result, Mapping):
        return None, "config and initial_result must be mappings"
    if (initial_result.get("phase") != "initial"
            or initial_result.get("status") not in ("GREEN", "YELLOW", "RED")
            or initial_result.get("validation", {}).get("status") != "COMPLETE"):
        return None, "A valid completed initial screen is required; a followup cannot authorize another"
    plan = initial_result.get("followup", {})
    if plan.get("campaigns_used", 1) != 0 or config["followup"]["max_campaigns"] != 1:
        return None, "The single bounded followup allowance has been consumed or is invalid"
    candidate, external = plan.get("selected_candidate"), plan.get("locked_external")
    candidates = initial_result.get("candidates", {})
    if candidate not in candidates or external not in config["external_comparators"]:
        return None, "No eligible locked followup candidate and external"
    primary, secondary = config["primary_candidate"], config["secondary_candidate"]
    expected = primary if candidates[primary]["color"] == "YELLOW" else (
        secondary if candidates[primary]["color"] == "GREEN" and candidates[secondary]["color"] == "YELLOW" else None)
    detail = candidates[candidate]
    prerequisites = (candidate == expected and detail["color"] == "YELLOW"
                     and plan["eligibility"][candidate]["eligible"]
                     and not detail["triggered_red_conditions"]
                     and detail["green_conditions"]["versus_matched_parent"]["pass"]
                     and detail["green_conditions"]["versus_TAIL"]["pass"]
                     and detail["locked_external"] == external
                     and initial_result["external_selection"]["selected"] == external)
    if not prerequisites:
        return None, "The original priority, component, TAIL or locked-external condition is not met"
    if plan.get("seeds") != config["followup"]["seeds"]:
        return None, "Followup seeds differ from the frozen plan"
    locks = {"locked_instances": [item["stem"] for item in config["instances"]],
             "locked_model": config["model"],
             "locked_primary_reference": config["metrics"]["primary_reference"],
             "locked_sensitivity_references": config["metrics"]["sensitivity_references"]}
    if any(plan.get(name) != value for name, value in locks.items()):
        return None, "Instances, model or references differ from the frozen initial screen"
    return (candidate, external), None

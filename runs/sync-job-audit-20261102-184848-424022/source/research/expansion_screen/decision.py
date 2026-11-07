"""Pure mathematical implementation of expansion-screen-v1.

Inputs contain already computed metrics, never archives or search callbacks.
The caller must establish implementation/protocol validity and persist whether
the one followup campaign has been consumed; this stateless module starts none.
"""

from collections.abc import Mapping

from ._criteria import followup_green_groups, initial_green_groups, initial_red_groups
from ._data import layout, validate_records
from ._metrics import compare, igd_guard_metrics, select_external
from ._followup import followup_plan, locked_authorization

INITIAL_SCOPE = ("Resource-allocation screen on six development instances; no significance, "
                 "unseen-instance generalization, novelty or publication-qualification claim")
FOLLOWUP_SCOPE = ("Limited scaling only against BASELINE and the initially locked external at 2T; "
                  "late-time superiority over all classical methods remains untested")


def _unclassified(status, phase, validation):
    return {"version": "expansion-screen-v1", "phase": phase, "status": status,
            "overall_color": None, "color": None, "validation": validation,
            "candidates": {}, "ready_for_step6": [], "scope": INITIAL_SCOPE,
            "followup": {"selected_candidate": None, "further_followup_allowed": False},
            "disposition": "REPAIR_PROTOCOL" if status == "INVALID" else "PAUSE_SCALING"}


def _evidence(index, candidate, external, config, instances, seeds, win_seeds, include_controls):
    labels = {"BASELINE": "BASELINE", "strongest_external": external}
    if include_controls:
        labels.update({"TAIL": "TAIL", "matched_parent": config["matched_parent"][candidate]})
    comparisons = {label: compare(index, candidate, comparator, instances, seeds, win_seeds=win_seeds)
                   for label, comparator in labels.items()}
    if include_controls:
        comparisons["all_external"] = {
            label: compare(index, candidate, label, instances, seeds, win_seeds=win_seeds)
            for label in config["external_comparators"]}
    sensitivity = {}
    for point in config["metrics"]["sensitivity_references"]:
        reference = str(point[0])
        sensitivity[reference] = {
            label: compare(index, candidate, labels[label], instances, seeds, reference, win_seeds=win_seeds)
            for label in ("BASELINE", "strongest_external")}
    igdplus = {label: igd_guard_metrics(index, candidate, labels[label], instances, seeds)
               for label in ("BASELINE", "strongest_external")}
    return comparisons, igdplus, sensitivity


def _candidate(index, label, external, config, instances, seeds):
    comparisons, igdplus, sensitivity = _evidence(
        index, label, external, config, instances, seeds, 3, include_controls=True)
    green = initial_green_groups(comparisons, igdplus, sensitivity, config)
    red = initial_red_groups(comparisons, config)
    red_reasons = [name for name, item in red.items() if item["pass"]]
    unmet = [name for name, item in green.items() if not item["pass"]]
    color = "RED" if red_reasons else "YELLOW" if unmet else "GREEN"
    return {"candidate": label, "color": color, "status": color,
            "locked_external": external, "comparisons": comparisons, "igdplus": igdplus,
            "sensitivity": sensitivity, "green_conditions": green, "red_conditions": red,
            "triggered_red_conditions": red_reasons, "unmet_green_conditions": unmet,
            "scope": "Pause this frozen configuration only" if color == "RED" else INITIAL_SCOPE}


def evaluate_screen(records, config, valid=True):
    """Classify the complete 270-cell initial matrix without running any search.

    ``valid`` is the caller's engineering/protocol acceptance, separate from the
    metric-shape checks here. Unknown cells, duplicates and malformed metrics
    are INVALID; missing cells alone are INSUFFICIENT_EVIDENCE.
    """
    if not valid:
        return _unclassified("INVALID", "initial", {"errors": ["Caller reported validity defect"]})
    if not isinstance(config, Mapping):
        return _unclassified("INVALID", "initial", {"errors": ["config must be a mapping"]})
    index, validation = validate_records(records, config)
    if validation["status"] != "COMPLETE":
        return _unclassified(validation["status"], "initial", validation)
    try:
        instances, _, seeds = layout(config)
        selection = select_external(index, config, instances, seeds)
        labels = (config["primary_candidate"], config["secondary_candidate"])
        candidates = {label: _candidate(index, label, selection["selected"], config, instances, seeds)
                      for label in labels}
        primary_color = candidates[labels[0]]["color"]
        result = {"version": config["version"], "phase": "initial", "status": primary_color,
                  "overall_color": primary_color, "color": primary_color,
                  "overall_color_basis": labels[0], "validation": validation,
                  "external_selection": selection, "candidates": candidates,
                  "ready_for_step6": [label for label in labels if candidates[label]["color"] == "GREEN"],
                  "scope": INITIAL_SCOPE, "p_value_hard_gate": False}
        result["followup"] = followup_plan(index, candidates, selection["selected"], config, instances, seeds)
        return result
    except (KeyError, TypeError, ValueError) as error:
        return _unclassified("INVALID", "initial", {**validation, "errors": [str(error)]})


def evaluate_followup(records, config, initial_result):
    """Use only the locked 3 variants x 6 instances x 3 new seeds at 2T.

    Passing the already consumed followup result back here cannot authorize a
    second campaign. Scheduling/persisting the single-use receipt is the
    caller's responsibility; reevaluation of the same evidence is harmless.
    """
    authorization, error = locked_authorization(config, initial_result)
    if error:
        result = _unclassified("INVALID", "followup", {"errors": [error]})
        result.update({"disposition": "PAUSE_SCALING", "scope": FOLLOWUP_SCOPE,
                       "campaigns_used": 1, "further_followup_allowed": False})
        return result
    candidate, external = authorization
    variants = [candidate, "BASELINE", external]
    seeds = config["followup"]["seeds"]
    index, validation = validate_records(records, config, variants, seeds, followup=True)
    if validation["status"] != "COMPLETE":
        result = _unclassified(validation["status"], "followup", validation)
        result.update({"scope": FOLLOWUP_SCOPE, "campaigns_used": 1,
                       "further_followup_allowed": False, "disposition": "PAUSE_SCALING"})
        return result
    instances, _, seeds = layout(config, variants, seeds)
    win_seeds = config["followup"]["bounded_continue_if_all"]["paired_positive_seed_count_per_win"]
    comparisons, igdplus, sensitivity = _evidence(
        index, candidate, external, config, instances, seeds, win_seeds, include_controls=False)
    parent_passed = initial_result["candidates"][candidate]["green_conditions"]["versus_matched_parent"]["pass"]
    conditions = followup_green_groups(comparisons, igdplus, sensitivity, parent_passed, config)
    unmet = [name for name, item in conditions.items() if not item["pass"]]
    status = "PAUSE" if unmet else "LIMITED_CONTINUE"
    color = "YELLOW" if unmet else "GREEN"
    detail = {"candidate": candidate, "status": status, "color": color, "locked_external": external,
              "comparisons": comparisons, "igdplus": igdplus, "sensitivity": sensitivity,
              "green_conditions": conditions, "unmet_green_conditions": unmet, "scope": FOLLOWUP_SCOPE}
    return {"version": config["version"], "phase": "followup", "status": status,
            "overall_color": color, "color": color, "validation": validation,
            "candidate": candidate, "locked_external": external, "candidates": {candidate: detail},
            "initial_seeds_used": False, "analysis_seeds": list(seeds), "time_multiplier": 2,
            "campaigns_used": 1, "further_followup_allowed": False,
            "ready_for_step6": [] if unmet else [candidate], "scope": FOLLOWUP_SCOPE,
            "disposition": "PAUSE_SCALING" if unmet else "LIMITED_SCALING_CONTINUE"}

"""Current v1 admission thresholds with explicitly named night controls."""
from research.expansion_screen._criteria import initial_green_groups, initial_red_groups


def admission(protocol, effects, selection):
    candidate, external = protocol["candidate"], selection["selected"]
    if external is None:
        return {"status": "UNRESOLVED_METRICS", "color": None, "admitted": False,
            "reason": "Global classical comparator could not be identified", "automaticFollowup": False}
    labels = {"BASELINE": protocol["baseline"], "TAIL": protocol["strong_control"],
        "matched_parent": protocol["matched_control"], "strongest_external": external}
    selected = {role: effects[candidate + "__vs__" + label] for role, label in labels.items()}
    final = {role: item["T"]["1.5"] for role, item in selected.items()}
    igd = {role: selected[role]["IGDplus"] for role in ("BASELINE", "strongest_external")}
    sensitivity = {point: {role: selected[role]["T"][point] for role in ("BASELINE", "strongest_external")}
        for point in ("1.25", "2.0")}
    all_metrics = list(final.values()) + list(igd.values())
    all_metrics += [metric for at_point in sensitivity.values() for metric in at_point.values()]
    if not all(metric["resolved"] for metric in all_metrics):
        return {"status": "UNRESOLVED_METRICS", "color": None, "admitted": False,
            "reason": "Degenerate or unresolved comparison; no epsilon imputation", "automaticFollowup": False}
    green = initial_green_groups(final, igd, sensitivity, protocol)
    green["validity_and_complete_campaign"] = green.pop("validity_and_complete_270_runs")
    green["validity_and_complete_campaign"]["expectedOwners"] = protocol["runs"]
    red = initial_red_groups(final, protocol)
    triggered, unmet = [key for key, value in red.items() if value["pass"]], [key for key, value in green.items() if not value["pass"]]
    color = "RED" if triggered else "YELLOW" if unmet else "GREEN"
    return {"status": color, "color": color, "admitted": color == "GREEN", "candidate": candidate,
        "locked_classic": external, "control_mapping": labels, "green_conditions": green, "red_conditions": red,
        "triggered_red_conditions": triggered, "unmet_green_conditions": unmet,
        "automaticFollowup": False, "formalStep6Started": False,
        "scope": "Current frozen configuration resource decision only; smaller mechanism effects do not grant scale-up qualification"}

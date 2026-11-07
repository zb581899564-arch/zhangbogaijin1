"""Observed admission-to-boundary provenance, without unsupported global acceptance claims."""
from collections import Counter, defaultdict

from analysis_tables import front_metrics
from report_io import identity, json_rows, require_linux


def _snapshot(row, run, context, ordinal):
    points = row["points"]
    keys = [point["key"] for point in points]
    values = [point["objectives"] for point in points]
    metrics = front_metrics(values, context)
    output = {**identity(run), "cycle": row["cycle"], "label": row["label"], "fe": row["fe"],
              "elapsedSeconds": row["elapsedSeconds"], "populationSize": len(points),
              "uniqueKeys": len(set(keys)), **metrics,
              "familyCounts": dict(Counter(str(point.get("family")) for point in points))}
    if run["arm"] == "GLOBAL_ONLY" and row["label"] == "POST_LOCAL" and not points:
        output["metricStatus"] = "EMPTY_EXPECTED_DISABLED_LOCAL"
    return {"ordinal": ordinal, "keys": set(keys), "objectives": set(map(tuple, values)), "row": output}


def _observed_membership(snapshot, admission, *, encoding=False):
    if snapshot is None or snapshot["ordinal"] <= admission["ordinal"]:
        return None, "MISSING_OR_PARTIAL_BOUNDARY"
    retained = (admission["point"]["key"] in snapshot["keys"] if encoding else
                tuple(admission["point"]["objectives"]) in snapshot["objectives"])
    return retained, "OBSERVED_BOUNDARY"


def _admission_rows(run, admissions, snapshots, accepted, final_front):
    final_objectives = set(map(tuple, final_front))
    result = []
    labels = {"INITIAL": "INITIAL", "GLOBAL": "POST_GLOBAL", "LOCAL": "POST_LOCAL"}
    for fe, admission in admissions.items():
        phase, cycle, point = admission["phase"], admission["cycle"], admission["point"]
        completed, completed_status = _observed_membership(snapshots.get((cycle, labels[phase])), admission)
        next_generation, next_status = _observed_membership(snapshots.get((cycle + 1, "PRE_GLOBAL")), admission)
        survivors, survivor_status = _observed_membership(snapshots.get((cycle, "SURVIVORS")), admission)
        completed_encoding, _ = _observed_membership(snapshots.get((cycle, labels[phase])), admission, encoding=True)
        next_encoding, _ = _observed_membership(snapshots.get((cycle + 1, "PRE_GLOBAL")), admission, encoding=True)
        survivor_encoding, _ = _observed_membership(snapshots.get((cycle, "SURVIVORS")), admission, encoding=True)
        local = accepted.get(fe)
        if phase != "LOCAL":
            local_status = "NOT_RECORDED_FOR_GLOBAL" if phase == "GLOBAL" else "NOT_APPLICABLE_INITIAL"
        else:
            local_status = "OBSERVED_LOCAL_DECISION" if local is not None else "MISSING_OR_PARTIAL_LOCAL_DECISION"
        result.append({**identity(run), "fe": fe, "cycle": cycle, "phase": phase,
                       "source": admission["source"], "role": admission["role"], "key": point["key"],
                       "family": point.get("family"),
                       **{name: point["objectives"][i] for i, name in enumerate(("Cmax", "TEC", "TWC"))},
                       "acceptedLocal": local["accepted"] if local is not None else None,
                       "acceptedLocalStatus": local_status,
                       "completedStageWorking": completed, "completedStageStatus": completed_status,
                       "completedStageEncodingRetained": completed_encoding,
                       "survivorBoundary": survivors, "survivorBoundaryStatus": survivor_status,
                       "survivorBoundaryEncodingRetained": survivor_encoding,
                       "nextGeneration": next_generation, "nextGenerationStatus": next_status,
                       "nextGenerationEncodingRetained": next_encoding,
                       "finalObjectiveRetained": tuple(point["objectives"]) in final_objectives})
    return result


def _summaries(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["phase"], row["source"])].append(row)
    result = []
    fields = ("acceptedLocal", "completedStageWorking", "survivorBoundary", "nextGeneration", "finalObjectiveRetained",
              "completedStageEncodingRetained", "survivorBoundaryEncodingRetained", "nextGenerationEncodingRetained")
    for (phase, source), selected in groups.items():
        row = {"phase": phase, "source": source, "admissionEvents": len(selected),
               "uniqueAdmittedKeys": len({item["key"] for item in selected}),
               "uniqueAdmittedObjectiveVectors": len({(item["Cmax"], item["TEC"], item["TWC"]) for item in selected})}
        for field in fields:
            row[field + "True"] = sum(item[field] is True for item in selected)
            row[field + "False"] = sum(item[field] is False for item in selected)
            row[field + "UnknownOrNotRecorded"] = sum(item[field] is None for item in selected)
        result.append(row)
    return result


def _transitions(run, snapshots, cycles):
    result = []
    for cycle in sorted(cycles):
        if cycle == 0:
            continue
        for phase, before_label, after_label in (("GLOBAL", "PRE_GLOBAL", "POST_GLOBAL"),
                                                 ("LOCAL", "POST_GLOBAL", "POST_LOCAL")):
            before, after = snapshots.get((cycle, before_label)), snapshots.get((cycle, after_label))
            disabled = (phase == "GLOBAL" and run["arm"] == "LOCAL_ONLY") or (phase == "LOCAL" and run["arm"] == "GLOBAL_ONLY")
            row = {**identity(run), "cycle": cycle, "phase": phase,
                   "beforeLabel": before_label, "afterLabel": after_label,
                   "status": "DISABLED_PHASE" if disabled else "COMPLETE_RECORDED_BOUNDARIES" if before and after else "PARTIAL_MISSING_BOUNDARY"}
            for metric in ("HV", "IGDplus", "IGD"):
                a = before["row"][metric] if before else None
                b = after["row"][metric] if after else None
                row[metric + "Before"], row[metric + "After"] = a, b
                row[metric + "AfterMinusBefore"] = b - a if a is not None and b is not None and not disabled else None
            result.append(row)
    return result


def inspect_provenance(run, context):
    require_linux()
    admissions, accepted, snapshots, selections = {}, {}, {}, []
    cycles, stop = set(), None
    previous_fe, previous_time = -1, -1.0
    for ordinal, row in enumerate(json_rows(run["path"] / "stage-events.jsonl")):
        if row["fe"] < previous_fe or row["elapsedSeconds"] < previous_time:
            raise ValueError("Stage events ran backward in paid FE or time")
        previous_fe, previous_time = row["fe"], row["elapsedSeconds"]
        cycles.add(row["cycle"])
        kind = row["kind"]
        if kind == "admission":
            if row["fe"] in admissions or row["phase"] not in ("INITIAL", "GLOBAL", "LOCAL"):
                raise ValueError("Duplicate admission FE or invalid producing phase")
            admissions[row["fe"]] = {**row, "ordinal": ordinal}
        elif kind == "workingAcceptance":
            fe = row["paidFE"]
            if fe in accepted or type(row["accepted"]) is not bool:
                raise ValueError("Invalid or duplicate local acceptance event")
            source = admissions.get(fe)
            if source is None or source["phase"] != "LOCAL" or source["point"]["key"] != row["point"]["key"]:
                raise ValueError("Local acceptance has no matching admitted paid point")
            accepted[fe] = row
        elif kind == "population":
            key = (row["cycle"], row["label"])
            if key in snapshots:
                raise ValueError("Duplicate population boundary")
            snapshots[key] = _snapshot(row, run, context, ordinal)
        elif kind == "selection":
            selected = row["selected"]
            if len(selected) != len(set(selected)) or any(index < 0 or index >= row["candidateCount"] for index in selected):
                raise ValueError("Invalid selected candidate indices")
            selections.append({**identity(run), "cycle": row["cycle"], "fe": row["fe"],
                               "candidateCount": row["candidateCount"], "selectedCount": len(selected),
                               "selected": selected, "quotas": row["quotas"]})
        elif kind == "stop":
            if stop is not None:
                raise ValueError("Duplicate stop event")
            stop = row
        else:
            raise ValueError("Unknown stage event kind: " + str(kind))
    if stop is None:
        raise ValueError("Missing terminal stop record")
    rows = _admission_rows(run, admissions, snapshots, accepted, run["front"])
    return {"admissions": admissions, "admissionRows": rows,
            "workingRows": [snapshot["row"] for snapshot in snapshots.values()],
            "transitionRows": _transitions(run, snapshots, cycles), "selectionRows": selections,
            "summaryRows": [{**identity(run), **row} for row in _summaries(rows)], "stop": stop,
            "limitations": ["No intermediate global QGS-batch working snapshots",
                            "Primary working/survivor/next-generation columns use complete objective tuples; EncodingRetained columns separately use exact keys",
                            "completedStageWorking false means absent at that boundary, not never accepted",
                            "Missing completed or next-generation boundary is unknown, not false",
                            "finalObjectiveRetained is exact objective membership, not encoding identity"]}

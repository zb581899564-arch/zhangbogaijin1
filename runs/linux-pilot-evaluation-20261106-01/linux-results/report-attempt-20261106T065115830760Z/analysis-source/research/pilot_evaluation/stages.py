"""Path-dependent HV accounting over the chronological paid-event prefix."""
from math import fsum, isclose

import numpy as np

from research.dynamic_benchmark.metrics import nondominated

from .indicators import hypervolume
from .validation import finite, integer, label, points, vector


def _counter():
    return {"event_count": 0, "positive_hv_events": 0, "delta_hv": 0.0}


def _add(counter, delta):
    counter["event_count"] += 1
    counter["positive_hv_events"] += int(delta > 0)
    counter["delta_hv"] += delta


def _validated_event(row, previous_event, previous_time, timed):
    event = integer(row["event"], "event", 1)
    if event <= previous_event:
        raise ValueError("Events must be strictly increasing; do not sort after reading outcomes")
    stage, source = label(row["stage"], "stage"), label(row["source"], "source")
    if stage.casefold() in ("sharing", "share"):
        raise ValueError("Sharing must be a nested flag inside its producing stage")
    if type(row.get("sharing")) is not bool:
        raise ValueError("Every event needs an explicit boolean sharing flag")
    objective = vector(row["objectives"])
    completed_at = None
    if timed:
        completed_at = finite(row["completed_at"], "completed_at")
        if completed_at < 0 or completed_at < previous_time:
            raise ValueError("Completion times must be nonnegative and nondecreasing")
    elif "completed_at" in row:
        raise ValueError("Use consistent time availability on every event")
    return event, stage, source, objective, completed_at


def _updated_archive(archive, point, reference, previous_hv):
    if len(archive) and np.any(np.all(archive <= point, axis=1)):
        return archive, previous_hv
    archive = nondominated(np.vstack((archive, point)))
    current_hv = hypervolume(archive, reference)
    if current_hv < previous_hv and not isclose(current_hv, previous_hv, rel_tol=1e-12, abs_tol=1e-12):
        raise ArithmeticError("Cumulative nondominated archive lost hypervolume")
    return archive, current_hv


def stage_hv_telescope(events, *, scale, hv_reference, initial_front=(),
                       until_event=None, until_time=None, keep_events=True):
    """Replay saved objective events, with sharing nested under each stage.

    Input: event (positive unique integer), objectives[3], stage, source,
    sharing (bool), and optionally completed_at (same unit as until_time).
    No final-front reference is used. The archive contains only the initial
    already-available front and consumed prefix. No scheduling model is called.
    """
    reference = vector(hv_reference)
    if until_event is not None:
        until_event = integer(until_event, "until_event")
    if until_time is not None:
        until_time = finite(until_time, "until_time")
        if until_time < 0:
            raise ValueError("until_time must be nonnegative")
    archive = nondominated(scale.normalize(points(initial_front)))
    initial_hv = current_hv = hypervolume(archive, reference)
    previous_event, previous_time, timed = 0, 0.0, None
    stages, trace, gains = {}, [], []
    total_events, last_event, last_time = 0, None, None
    for row in events:
        if timed is None:
            timed = "completed_at" in row
            if until_time is not None and not timed:
                raise ValueError("Time cutoff requires a completion time on each event")
        event, stage, source, raw, completed_at = _validated_event(row, previous_event, previous_time, timed)
        if (until_event is not None and event > until_event) or (
                until_time is not None and completed_at > until_time):
            break
        previous_event, previous_time = event, completed_at if timed else 0.0
        before = current_hv
        archive, current_hv = _updated_archive(archive, scale.normalize([raw])[0], reference, before)
        delta = current_hv - before
        gains.append(delta)
        total_events += 1
        last_event, last_time = event, completed_at
        bucket = stages.setdefault(stage, {**_counter(), "sharing": _counter(), "by_source": {}})
        _add(bucket, delta)
        _add(bucket["by_source"].setdefault(source, _counter()), delta)
        if row["sharing"]:
            _add(bucket["sharing"], delta)
        if keep_events:
            trace.append({"event": event, "stage": stage, "source": source, "sharing": row["sharing"],
                          "completed_at": completed_at, "hv_before": before,
                          "hv_after": current_hv, "delta_hv": delta})
    total_gain, summed_gain = current_hv - initial_hv, fsum(gains)
    stage_gain = fsum(bucket["delta_hv"] for bucket in stages.values())
    if not isclose(summed_gain, total_gain, rel_tol=1e-10, abs_tol=1e-12) or not isclose(
            stage_gain, total_gain, rel_tol=1e-10, abs_tol=1e-12):
        raise ArithmeticError("Stage HV increments failed the chronological telescope")
    return {"initial_hv": initial_hv, "final_hv": current_hv, "total_delta_hv": total_gain,
            "sum_event_delta_hv": summed_gain, "sum_stage_delta_hv": stage_gain,
            "event_count": total_events, "last_event": last_event, "last_completed_at": last_time,
            "by_stage": stages, "events": trace,
            "attribution": "Chronological descriptive increments; sharing is a subset, not an extra stage",
            "causal_claim": False}

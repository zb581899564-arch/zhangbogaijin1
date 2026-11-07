"""Exact admitted-event HV telescope and inclusive phase/source cost accounting."""
import csv
import math
from collections import Counter

from research.pilot_evaluation import hypervolume, stage_hv_telescope
from report_io import identity, require_linux
from exact_hv import exact_hv


def _admitted_events(run, admissions, counters):
    last_fe, last_time, seen = 0, -1.0, set()
    with (run["path"] / "paid-events.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            fe, elapsed = int(row["fe"]), float(row["elapsedSeconds"])
            phase, source = row["stage"], row["source"]
            objective = [float(row[name]) for name in ("Cmax", "TEC", "TWC")]
            if fe != last_fe + 1 or elapsed < last_time or not all(map(math.isfinite, [elapsed, *objective])):
                raise ValueError("Paid ledger contains a gap, reversed time or nonfinite value")
            if phase not in ("INITIAL", "GLOBAL", "LOCAL") or row["admitted"] not in ("0", "1"):
                raise ValueError("Invalid paid phase or admitted flag")
            shared = source == "SHARED_COMPOSITION"
            if shared and phase != "GLOBAL":
                raise ValueError("Sharing escaped its GLOBAL parent stage")
            counters[phase] += 1
            counters[(phase, source)] += 1
            last_fe, last_time = fe, elapsed
            admitted = row["admitted"] == "1"
            if admitted != (fe in admissions):
                raise ValueError("Paid CSV and admission JSONL disagree")
            if not admitted:
                continue
            witness = admissions[fe]
            if (witness["phase"] != phase or witness["source"] != source or
                    witness["point"]["objectives"] != objective or int(row["cycle"]) != witness["cycle"]):
                raise ValueError("Admission source/objective witness differs from paid CSV")
            seen.add(fe)
            yield {"event": fe, "objectives": objective, "stage": phase,
                   "source": source, "sharing": shared, "completed_at": elapsed}
    if last_fe != run["receipt"]["successful"] or seen != set(admissions):
        raise ValueError("Incomplete paid ledger or unpaired admission witness")


def _ratio(value, denominator):
    return value / denominator if denominator > 0 else None


def stage_costs(run, context, admissions):
    require_linux()
    counters = Counter()
    ledger = stage_hv_telescope(_admitted_events(run, admissions, counters), scale=context["scale"],
                               hv_reference=context["hv_reference"], keep_events=False, hv_calculator=exact_hv)
    expected = hypervolume(context["scale"].normalize(run["front"]), context["hv_reference"])
    if not math.isclose(ledger["final_hv"], expected, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError("Admitted-prefix telescope disagrees with final saved-front HV")
    trace = run["receipt"]["trace"]
    for phase in ("INITIAL", "GLOBAL", "LOCAL", "LIFECYCLE"):
        if trace["phaseFE"].get(phase, 0) != counters[phase]:
            raise ValueError("Paid ledger phase FE differs from receipt")
    for (phase, source), count in ((key, value) for key, value in counters.items() if isinstance(key, tuple)):
        if trace["phaseFE"].get(phase + "/" + source, 0) != count:
            raise ValueError("Paid ledger source FE differs from receipt")
    rows, sources = [], []
    for phase in ("INITIAL", "GLOBAL", "LOCAL", "LIFECYCLE"):
        bucket = ledger["by_stage"].get(phase, {})
        gain = bucket.get("delta_hv", 0.0)
        seconds = trace["phaseSecondsInclusive"].get(phase, 0.0)
        observation = trace["observationNanosByPhase"].get(phase, 0) / 1e9
        net = seconds - observation
        sharing = bucket.get("sharing", {})
        row = {**identity(run), "phase": phase, "successfulFE": counters[phase],
               "admittedEvents": bucket.get("event_count", 0), "deltaHV": gain,
               "secondsInclusive": seconds, "traceObservationSeconds": observation,
               "netTraceSubtractionReferenceSeconds": net if net >= 0 else None,
               "deltaHVPerFE": _ratio(gain, counters[phase]),
               "deltaHVPer10000FE": _ratio(10000 * gain, counters[phase]),
               "deltaHVPerInclusiveSecond": _ratio(gain, seconds),
               "sharedSubsetFE": counters[(phase, "SHARED_COMPOSITION")],
               "sharedSubsetAdmittedEvents": sharing.get("event_count", 0),
               "sharedSubsetDeltaHV": sharing.get("delta_hv", 0.0),
               "sharedSubsetDeltaHVPerFE": _ratio(sharing.get("delta_hv", 0.0), counters[(phase, "SHARED_COMPOSITION")]),
               "sharedSubsetSeconds": None,
               "timeNote": "Phase trace subtraction only; checkpoint observation is not allocated by phase"}
        rows.append(row)
        for key, count in counters.copy().items():
            if not isinstance(key, tuple) or key[0] != phase or count == 0:
                continue
            source = key[1]
            data = bucket.get("by_source", {}).get(source, {})
            sources.append({**identity(run), "phase": phase, "source": source,
                            "successfulFE": count, "admittedEvents": data.get("event_count", 0),
                            "deltaHV": data.get("delta_hv", 0.0),
                            "nestedSharingSubset": source == "SHARED_COMPOSITION"})
    ledger.update(identity(run))
    ledger["inclusivePhaseSecondsMinusSearchSeconds"] = sum(trace["phaseSecondsInclusive"].values()) - run["receipt"]["searchSeconds"]
    ledger["initialIncludedAndSeparate"] = True
    return rows, sources, ledger

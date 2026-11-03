"""Validate complete renewal counters and a bounded first4+last4+partial trace."""
from pathlib import Path
from research.semantic_repair.trials import json_lines
from .validation import integer
from .context_events import validate_event

SAMPLE_POLICY = "first4+last4 completed events plus current partial event"
FREQUENCY = "One round-robin family at generation start after first completed generation"
HISTORY_POLICY = "Reset all five personal histories after charged reevaluation; keep legitimate global archive"


def require_contracts(protocol):
    for spec in protocol["variants"].values():
        if spec.get("observation") == {"schema": "factory-transfer-v1"}:
            from .factory_transfer import require_contract
            require_contract()
            continue
        if spec.get("observation") not in (None, {"schema": "context-renewal-v1"}):
            raise ValueError("Unknown bounded mechanism observation schema")
    from .checkpoint_evidence import require_contract
    require_contract(protocol)


def validate_counters(counters, summary, mode):
    if counters.get("mode") != mode or counters.get("samplePolicy") != SAMPLE_POLICY:
        raise ValueError("Context mode or bounded sample policy changed")
    if counters.get("refreshFrequency") != FREQUENCY or counters.get("historyPolicy") != HISTORY_POLICY:
        raise ValueError("Context refresh frequency or personal-history policy changed")
    for key in ("eventsStarted", "eventsCompleted", "paidResetEvaluations", "skippedNoNovelFreeFA", "pendingResetEvaluations"):
        integer(counters.get(key), key)
    started, completed, pending = (counters[key] for key in ("eventsStarted", "eventsCompleted", "pendingResetEvaluations"))
    if pending > 5 or started != completed + (pending > 0):
        raise ValueError("Context event completion/pending counters do not close")
    expected_paid = 5 * completed + (5 - pending if pending else 0)
    if counters["paidResetEvaluations"] != expected_paid:
        raise ValueError("Context reset FE counter does not include exactly completed and partial events")
    for key in ("context-renewal.evaluations", "context-renewal.personalHistoriesReset"):
        if summary.get("search", {}).get(key, 0) != expected_paid:
            raise ValueError("Context reset cost/history count differs from actual canonical search: " + key)


def _continuity(events):
    epochs, previous = {}, None
    for row in events:
        family, epoch = row["family"], row["epoch"]
        if family in epochs and epoch <= epochs[family]:
            raise ValueError("Context epoch did not increase for its family")
        if row["event"] <= 4 and epoch != epochs.get(family, 0) + 1:
            raise ValueError("First captured context events skipped a family epoch")
        epochs[family] = epoch
        if previous:
            if row["generation"] <= previous["generation"] or row["startFE"] < previous["endFE"]:
                raise ValueError("Sampled renewal events are not chronologically ordered")
            if row["event"] == previous["event"] + 1:
                expected = [list(value) for value in previous["previousFactoryAssignments"]]
                expected[previous["family"]] = previous["newFactoryByJob"]
                if row["previousFactoryAssignments"] != expected:
                    raise ValueError("Consecutive renewal events lost a context or retained a replaced FA")
        previous = row


def validate_observation(rows, summary, mode):
    counters = summary.get("cooperation", {}).get("contextRenewal")
    if not isinstance(counters, dict):
        raise ValueError("Missing summary.cooperation.contextRenewal")
    validate_counters(counters, summary, mode)
    if not rows or rows[0].get("type") != "context-renewal-summary":
        raise ValueError("Missing context-renewal summary header")
    if {key: value for key, value in rows[0].items() if key != "type"} != counters:
        raise ValueError("Context trace header differs from the complete summary counters")
    complete = counters["eventsCompleted"]
    expected = list(range(1, min(complete, 4) + 1))
    expected += list(range(max(5, complete - 3), complete + 1))
    if counters["pendingResetEvaluations"]:
        expected.append(counters["eventsStarted"])
    events = rows[1:]
    if len(events) > 9 or [row.get("event") for row in events] != expected:
        raise ValueError("Context trace escaped first4+last4+current-partial capture")
    checked = [validate_event(row, mode, summary) for row in events]
    if any(not row["complete"] for row in checked[:-1]):
        raise ValueError("Only the current final renewal event may be partial")
    if checked and not checked[-1]["complete"]:
        if checked[-1]["successfulResetEvaluations"] != 5 - counters["pendingResetEvaluations"]:
            raise ValueError("Current partial event differs from pending reset count")
    _continuity(events)
    return {"schema": "context-renewal-v1", "completeSearchCounters": counters,
        "sampledEvents": checked, "deadlineValidSampledCompletedEvents": sum(row["deadlineValidCompleted"] for row in checked),
        "sampledEventsEndedAfterT": sum(row["endedAfterT"] for row in checked),
        "scope": "Full counters span search; only bounded events witnessed. Above-T events are not deadline-valid contributions; no descendant attribution."}


def attach_observation(run, spec):
    expected = spec.get("observation")
    if expected == {"schema": "factory-transfer-v1"}:
        from .factory_transfer import attach
        attach(run, spec)
        return
    actual = run["summary"].get("cooperation", {}).get("contextRenewal")
    path = Path(run["folder"]) / "context-renewal.jsonl"
    if run["summary"].get("cooperation", {}).get("factoryTransfer") is not None or (Path(run["folder"]) / "factory-transfer.jsonl").exists():
        raise ValueError("Non-H2 method unexpectedly enabled factory transfer")
    if expected is None:
        if actual is not None or path.exists():
            raise ValueError("Static/classical control unexpectedly enabled context renewal")
        run["mechanismObservation"] = None
        return
    if expected != {"schema": "context-renewal-v1"}:
        raise ValueError("Unknown mechanism observation schema")
    mode = "ELITE" if spec["mode"].endswith("_CONTEXT_ELITE") else "RANDOM" if spec["mode"].endswith("_CONTEXT_RANDOM") else None
    if mode is None:
        raise ValueError("Renewal observation attached to an unregistered mechanism mode")
    run["mechanismObservation"] = validate_observation(json_lines(path), run["summary"], mode)

"""Independently reconstruct the factory-local packet/mosaic encoding witnesses."""
from .validation import integer, nonnegative, objectives
from .instance_contract import dimensions

DIRECTIONS = {"MAKESPAN": 0, "ENERGY": 1, "WORKER_COST": 2}
ENCODING_KEYS = ("jobs", "machines", "workers")


def encoding(record, jobs, name):
    local = {}
    for key in ENCODING_KEYS:
        values = record.get(key)
        if not isinstance(values, list) or not values:
            raise ValueError("Missing factory-local vector: " + name + "." + key)
        for value in values:
            integer(value, name + "." + key, 0, jobs - 1 if key == "jobs" else None)
        local[key] = values
    if len(set(local["jobs"])) != len(local["jobs"]) or any(len(local[key]) != len(local["jobs"]) for key in ENCODING_KEYS):
        raise ValueError("Factory-local encoding has duplicated jobs or misaligned resources")
    return local


def validate_source(record, actual_jobs, event, jobs):
    local = encoding(record, jobs, "paid source")
    if set(local["jobs"]) != actual_jobs:
        raise ValueError("Source record escaped the current factory job set")
    objectives(record.get("objectives"), "paid source objectives")
    integer(record.get("paidFE"), "source paidFE", 1, event["proposalFE"])
    integer(record.get("generation"), "source generation", 0, event["generation"])
    if any(not isinstance(record.get(key), str) or not record[key] for key in ("producer", "stage")):
        raise ValueError("Source record omitted its paid producer/stage provenance")


def selected_sources(row, mode, jobs, actual_jobs):
    pairs = row.get("sampledPairs")
    if not isinstance(pairs, list) or len(pairs) != 3:
        raise ValueError("Exactly three source pairs and six draws are required")
    objective = DIRECTIONS[row["direction"]]
    selected, by_ordinal = [], {}
    for pair in pairs:
        for side in ("first", "second"):
            ordinal = integer(pair.get(side + "Ordinal"), side + "Ordinal")
            record = pair.get(side)
            if not isinstance(record, dict):
                raise ValueError("Missing sampled source record")
            validate_source(record, actual_jobs, row, jobs)
            if ordinal in by_ordinal and by_ordinal[ordinal] != record:
                raise ValueError("One immutable pool ordinal produced different records in one proposal")
            by_ordinal[ordinal] = record
        second = mode.endswith("ROLE") and pair["second"]["objectives"][objective] < pair["first"]["objectives"][objective]
        if type(pair.get("selectedSecond")) is not bool or pair["selectedSecond"] != second:
            raise ValueError("ROLE/RANDOM source selection differs from independent objective replay")
        selected.append(pair["second"] if second else pair["first"])
    if row.get("source0") != selected[0]:
        raise ValueError("source0 differs from the first independently selected source")
    return selected


def expected_encoding(selected, mode):
    sequence = selected[0]["jobs"]
    machine_source = selected[0] if mode.startswith("PACKET") else selected[1]
    worker_source = selected[0] if mode.startswith("PACKET") else selected[2]
    machines = dict(zip(machine_source["jobs"], machine_source["machines"]))
    workers = dict(zip(worker_source["jobs"], worker_source["workers"]))
    return {"jobs": sequence, "machines": [machines[job] for job in sequence],
        "workers": [workers[job] for job in sequence]}


def validate_event(row, mode, summary):
    if row.get("type") != "factory-transfer-paid" or row.get("mode") != mode:
        raise ValueError("Factory transfer event type or mode differs")
    integer(row.get("event"), "transfer event", 1)
    integer(row.get("family"), "transfer family", 0, 3)
    integer(row.get("generation"), "transfer generation", 1)
    shape = dimensions(summary["instance"])
    jobs, factories = shape.jobs, shape.factories
    integer(row.get("factory"), "transfer factory", 0, factories - 1)
    if row.get("direction") not in DIRECTIONS:
        raise ValueError("CENTER or unknown direction triggered a new factory transfer")
    proposal = integer(row.get("proposalFE"), "proposalFE", 1)
    paid = integer(row.get("paidFE"), "paidFE", 1, summary["successful"])
    if paid != proposal + 1:
        raise ValueError("Factory transfer hid an evaluation or failed to charge a duplicate")
    seconds = nonnegative(row.get("elapsedSeconds"), "transfer elapsedSeconds")
    deadline_valid = seconds <= summary["timeLimitSeconds"]
    if type(row.get("deadlineValid")) is not bool or row["deadlineValid"] != deadline_valid:
        raise ValueError("Factory transfer deadline witness differs from its timestamp")
    objectives(row.get("parentObjectives"), "transfer parent objectives")
    objectives(row.get("objectives"), "transfer child objectives")
    actual_record = row.get("actualLocal")
    if not isinstance(actual_record, dict):
        raise ValueError("Missing actual decoded local factory record")
    actual = encoding(actual_record, jobs, "actualLocal")
    objectives(actual_record.get("objectives"), "actual local objectives")
    selected = selected_sources(row, mode, jobs, set(actual["jobs"]))
    expected = expected_encoding(selected, mode)
    before = encoding(row.get("beforeRepairLocal", {}), jobs, "beforeRepairLocal")
    if expected != before or expected != actual:
        raise ValueError("Expected source tuple, pre-repair encoding and actual local encoding differ")
    intact = actual == {key: selected[0][key] for key in ENCODING_KEYS}
    if type(row.get("source0EncodingPreserved")) is not bool or row["source0EncodingPreserved"] != intact:
        raise ValueError("Source0 encoding-preservation witness differs from independent reconstruction")
    timeline = row.get("source0TimelineMatched")
    if type(timeline) is not bool or intact and not timeline:
        raise ValueError("An intact local encoding lost its Java timeline witness")
    if mode.startswith("PACKET") and not intact:
        raise ValueError("PACKET fragmented the chosen source0 tuple")
    if row.get("otherFactoriesPreserved") is not True:
        raise ValueError("Java full-parent comparison did not preserve other factories")
    return {"event": row["event"], "paidFE": paid, "generation": row["generation"],
        "elapsedSeconds": seconds,
        "deadlineValid": deadline_valid, "source0EncodingPreserved": intact, "source0TimelineMatched": timeline,
        "otherFactoriesPreservedWitness": True,
        "scope": "Independent local encoding/source replay; timeline and other factories are accepted Java witnesses, not an offline full-parent reconstruction"}

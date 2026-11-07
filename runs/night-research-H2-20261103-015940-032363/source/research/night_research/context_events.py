"""Replay one bounded context-renewal event without invoking the scheduling model."""
from .validation import integer, nonnegative, objectives, indices
from .instance_contract import dimensions


def center_order(points):
    def dominates(a, b):
        return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))
    fitness = []
    for point in points:
        p = sum(dominates(point, other) for other in points)
        q = sum(dominates(other, point) for other in points)
        fitness.append(q + 1. / (p + 1))
    return sorted(range(len(points)), key=lambda i: fitness[i])


def _assignment(value, name, jobs, factories):
    if not isinstance(value, list) or len(value) != jobs:
        raise ValueError("FA-by-job size changed: " + name)
    for factory in value:
        integer(factory, name, 0, factories - 1)
    if set(value) != set(range(factories)):
        raise ValueError("Context emptied a factory: " + name)
    return value


def _selection(row, mode):
    count = integer(row["candidateCount"], "candidateCount", 1, 80)
    candidates = indices(row["candidatePopulationIndices"], "candidatePopulationIndices", count, 100)
    values = row["candidateObjectives"]
    if not isinstance(values, list) or len(values) != count:
        raise ValueError("Candidate objectives do not cover the complete eligible pool")
    for value in values:
        objectives(value, "candidateObjectives")
    ranked = center_order(values)
    if row["rankedCandidateOrdinals"] != ranked:
        raise ValueError("CENTER PDDR stable ranking differs from independent replay")
    random = integer(row["randomCandidateOrdinal"], "randomCandidateOrdinal", 0, count - 1)
    selected = integer(row["selectedCandidateOrdinal"], "selectedCandidateOrdinal", 0, count - 1)
    if selected != (ranked[0] if mode == "ELITE" else random):
        raise ValueError("ELITE/RANDOM selected ordinal differs from its registered control")
    if row["donorPopulationIndex"] != candidates[selected] or row["donorObjectives"] != values[selected]:
        raise ValueError("Donor does not match the selected current-free candidate witness")
    particles = indices(row["particleIndices"], "particleIndices", 5, 100)
    if set(particles).intersection(candidates):
        raise ValueError("Family reset particles overlap the free donor pool")
    if row.get("sourceIsCurrentFreeParticle") is not True or row.get("donorFamily") != -1:
        raise ValueError("Donor is not witnessed as a current free particle")


def validate_event(row, mode, summary):
    if row.get("type") != "context-renewal" or row.get("mode") != mode:
        raise ValueError("Context event type or mode differs")
    event = integer(row["event"], "event", 1)
    generation = integer(row["generation"], "generation", 2)
    family = integer(row["family"], "family", 0, 3)
    if family != (generation - 2) % 4:
        raise ValueError("Context renewal escaped the round-robin generation rule")
    integer(row["epoch"], "epoch", 1, event)
    shape = dimensions(summary["instance"])
    jobs, factories = shape.jobs, shape.factories
    previous = row["previousFactoryAssignments"]
    if not isinstance(previous, list) or len(previous) != 4:
        raise ValueError("All four previous contexts are required")
    for value in previous:
        _assignment(value, "previousFactoryAssignments", jobs, factories)
    old = _assignment(row["oldFactoryByJob"], "oldFactoryByJob", jobs, factories)
    new = _assignment(row["newFactoryByJob"], "newFactoryByJob", jobs, factories)
    if old != previous[family] or any(new == value for value in previous):
        raise ValueError("Renewal failed to leave all four old FA contexts")
    _selection(row, mode)
    integer(row["clearedPoolRecords"], "clearedPoolRecords")
    if row.get("expectedResetEvaluations") != 5 or type(row.get("complete")) is not bool:
        raise ValueError("Context reset size or completion marker changed")
    paid = integer(row["successfulResetEvaluations"], "successfulResetEvaluations", 0, 5)
    start, end = integer(row["startFE"], "startFE"), integer(row["endFE"], "endFE")
    if end != start + paid or end > summary["successful"] or row["complete"] != (paid == 5):
        raise ValueError("Context reset hid an evaluation or fabricated full completion")
    begin, finish = nonnegative(row["startedSeconds"], "startedSeconds"), nonnegative(row["endedSeconds"], "endedSeconds")
    if finish < begin:
        raise ValueError("Context event ran backwards in time")
    values = row["newObjectives"]
    if not isinstance(values, list) or len(values) != paid:
        raise ValueError("Reset objective triples differ from successful charged resets")
    for value in values:
        objectives(value, "newObjectives")
    return {"event": event, "family": family, "epoch": row["epoch"], "generation": generation,
        "successfulResetEvaluations": paid, "complete": row["complete"],
        "deadlineValidCompleted": row["complete"] and finish <= summary["timeLimitSeconds"],
        "startedAfterT": begin > summary["timeLimitSeconds"], "endedAfterT": finish > summary["timeLimitSeconds"],
        "sourceEvidence": "Current-free source witness plus accepted Java implementation; full population not reconstructed offline"}

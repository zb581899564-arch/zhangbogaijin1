"""Small fixed packet/mosaic witnesses and actual opportunity-count checks."""
from copy import deepcopy
from .factory_transfer import validate_observation, SAMPLE_POLICY, MARGINALS


def fixture(mode="PACKET_ROLE", late=False):
    def record(jobs, machines, workers, value, fee):
        return {"jobs": jobs, "machines": machines, "workers": workers, "objectives": [value] * 3,
            "paidFE": fee, "generation": 0, "producer": "INITIALIZATION", "stage": "initialization"}
    a = record([0, 1, 2], [0, 0, 0], [0, 0, 0], 3., 1)
    b = record([2, 0, 1], [1, 1, 1], [1, 1, 1], 2., 2)
    c = record([1, 2, 0], [2, 0, 1], [2, 0, 1], 1., 3)
    role, packet = mode.endswith("ROLE"), mode.startswith("PACKET")
    pairs = [{"firstOrdinal": i, "secondOrdinal": j, "first": first, "second": second,
        "selectedSecond": role and second["objectives"][0] < first["objectives"][0]}
        for i, j, first, second in ((0, 1, a, b), (1, 2, b, c), (2, 0, c, a))]
    if mode == "PACKET_ROLE":
        local = {"jobs": [2, 0, 1], "machines": [1, 1, 1], "workers": [1, 1, 1]}
    elif mode == "MOSAIC_ROLE":
        local = {"jobs": [2, 0, 1], "machines": [0, 1, 2], "workers": [0, 1, 2]}
    elif mode == "PACKET_RANDOM":
        local = {"jobs": [0, 1, 2], "machines": [0, 0, 0], "workers": [0, 0, 0]}
    else:
        local = {"jobs": [0, 1, 2], "machines": [1, 1, 1], "workers": [1, 2, 0]}
    cells = [{"family": family, "direction": direction, "opportunities": 4 if family == 0 and direction == "MAKESPAN" else 0}
        for family in range(4) for direction in ("MAKESPAN", "ENERGY", "WORKER_COST")]
    counters = {"mode": mode, "eligibleOpportunities": 4, "scheduledAttempts": 1, "sourceRandomDraws": 6,
        "paidTransfers": 1, "deadlineValidPaidTransfers": int(not late), "source0EncodingPreserved": int(packet),
        "source0TimelineMatched": int(packet), "otherFactoriesPreserved": 1, "pendingTransfers": 0,
        "samplePolicy": SAMPLE_POLICY, "duplicatesArePaid": True, "sourceMarginals": MARGINALS, "perFamilyDirection": cells}
    summary = {"instance": "3_1_3_1.txt", "successful": 11, "timeLimitSeconds": 1., "cooperation": {"factoryTransfer": counters}}
    row = {"type": "factory-transfer-paid", "event": 1, "mode": mode, "family": 0, "factory": 0,
        "direction": "MAKESPAN", "generation": 1, "proposalFE": 10, "paidFE": 11,
        "elapsedSeconds": 1.01 if late else .8, "deadlineValid": not late,
        "parentObjectives": [4.] * 3, "objectives": [2.] * 3, "sampledPairs": pairs,
        "source0": b if role else a, "beforeRepairLocal": local,
        "actualLocal": {**local, "objectives": [2.] * 3, "paidFE": -1, "generation": -1, "producer": "NONE", "stage": "untracked"},
        "source0EncodingPreserved": packet, "source0TimelineMatched": packet, "otherFactoriesPreserved": True}
    return [{"type": "factory-transfer-summary", **counters}, row], summary


def _reject(rows, summary, mode="PACKET_ROLE"):
    try:
        validate_observation(rows, summary, mode)
    except ValueError:
        return
    raise AssertionError("Malformed transfer witness was accepted")


def run_transfer_checks():
    for mode in ("PACKET_ROLE", "MOSAIC_ROLE", "PACKET_RANDOM", "MOSAIC_RANDOM"):
        rows, summary = fixture(mode)
        assert validate_observation(rows, summary, mode)["sampledDeadlineValidEvents"] == 1
    rows, summary = fixture(late=True)
    assert validate_observation(rows, summary, "PACKET_ROLE")["sampledDeadlineValidEvents"] == 0
    rows, summary = fixture("MOSAIC_ROLE")
    rows[1]["source0TimelineMatched"] = True
    summary["cooperation"]["factoryTransfer"]["source0TimelineMatched"] = rows[0]["source0TimelineMatched"] = 1
    assert validate_observation(rows, summary, "MOSAIC_ROLE")["sampledEvents"][0]["source0TimelineMatched"]
    rows, summary = fixture()
    wrong = deepcopy(rows)
    wrong[1]["sampledPairs"][0]["selectedSecond"] = False
    _reject(wrong, summary)
    wrong = deepcopy(rows)
    wrong[1]["actualLocal"]["machines"][0] = 9
    _reject(wrong, summary)
    wrong = deepcopy(rows)
    wrong[1]["sampledPairs"][0]["first"]["paidFE"] = 11
    _reject(wrong, summary)
    wrong_summary = deepcopy(summary)
    wrong_summary["cooperation"]["factoryTransfer"]["sourceRandomDraws"] = 3
    _reject(rows, wrong_summary)
    wrong = deepcopy(rows)
    wrong[1]["direction"] = "CENTER"
    _reject(wrong, summary)
    # Repeated child objectives are still one charged transfer.
    rows[1]["objectives"] = rows[1]["parentObjectives"]
    assert validate_observation(rows, summary, "PACKET_ROLE")["completeSearchCounters"]["paidTransfers"] == 1
    counters = deepcopy(summary["cooperation"]["factoryTransfer"])
    for key in ("scheduledAttempts", "sourceRandomDraws", "paidTransfers", "deadlineValidPaidTransfers",
                "source0EncodingPreserved", "source0TimelineMatched", "otherFactoriesPreserved"):
        counters[key] = 0
    counters["perFamilyDirection"][0]["opportunities"] = 2
    counters["perFamilyDirection"][1]["opportunities"] = 2
    empty_summary = {**summary, "cooperation": {"factoryTransfer": counters}}
    assert validate_observation([{"type": "factory-transfer-summary", **counters}], empty_summary, "PACKET_ROLE")
    counters["perFamilyDirection"][0]["opportunities"] = 4
    counters["perFamilyDirection"][1]["opportunities"] = 0
    counters.update({"scheduledAttempts": 1, "sourceRandomDraws": 6, "pendingTransfers": 1})
    assert validate_observation([{"type": "factory-transfer-summary", **counters}], empty_summary, "PACKET_ROLE")
    base, large_summary = fixture()
    large = large_summary["cooperation"]["factoryTransfer"]
    large.update({"eligibleOpportunities": 80, "scheduledAttempts": 20, "sourceRandomDraws": 120,
        "paidTransfers": 20, "deadlineValidPaidTransfers": 20, "source0EncodingPreserved": 20,
        "source0TimelineMatched": 20, "otherFactoriesPreserved": 20})
    large["perFamilyDirection"][0]["opportunities"] = 80
    large_summary["successful"] = 121
    sampled = [{"type": "factory-transfer-summary", **large}]
    for event in [*range(1, 9), *range(13, 21)]:
        row = deepcopy(base[1])
        row.update({"event": event, "proposalFE": 100 + event, "paidFE": 101 + event,
            "generation": 2 + event // 10, "elapsedSeconds": .1 + event / 1000})
        sampled.append(row)
    assert len(validate_observation(sampled, large_summary, "PACKET_ROLE")["sampledEvents"]) == 16
    _reject(sampled[:-1], large_summary)
    return {"allFourSourceEncodingsReconstructed": True, "actualLocalUntrackedMetadataAllowed": True,
        "mosaicSameTimelineWithoutSameEncodingAllowed": True, "latePaidEventsRetained": True,
        "futureSourcesWrongDrawsAndCENTERRejected": True, "duplicatesCharged": True,
        "frequencyIsPerFamilyDirectionNotGlobalFloor": True, "pendingTransferAccepted": True,
        "first8Last8BoundsReplayed": True}

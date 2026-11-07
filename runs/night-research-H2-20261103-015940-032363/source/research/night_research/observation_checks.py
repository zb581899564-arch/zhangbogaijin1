"""Small renewal evidence fixtures: ranking, charged partial resets and novelty."""
from copy import deepcopy
from .observations import validate_observation, SAMPLE_POLICY, FREQUENCY, HISTORY_POLICY


def fixture(mode="ELITE", paid=5):
    previous = [[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]]
    values = [[3., 3., 3.], [1., 1., 1.], [1., 1., 1.]]
    selected = 1 if mode == "ELITE" else 2
    complete = paid == 5
    counters = {"mode": mode, "eventsStarted": 1, "eventsCompleted": int(complete), "paidResetEvaluations": paid,
        "skippedNoNovelFreeFA": 0, "pendingResetEvaluations": 5 - paid,
        "refreshFrequency": FREQUENCY, "historyPolicy": HISTORY_POLICY, "samplePolicy": SAMPLE_POLICY}
    summary = {"instance": "4_3_2_1.txt", "successful": 100 + paid, "timeLimitSeconds": 1.,
        "search": {"context-renewal.evaluations": paid, "context-renewal.personalHistoriesReset": paid},
        "cooperation": {"contextRenewal": counters}}
    row = {"type": "context-renewal", "event": 1, "mode": mode, "generation": 2, "family": 0, "epoch": 1,
        "startFE": 100, "endFE": 100 + paid, "startedSeconds": .8, "endedSeconds": .9 if complete else 1.01,
        "sourceIsCurrentFreeParticle": True, "donorPopulationIndex": 20 + selected,
        "candidateCount": 3, "randomCandidateOrdinal": 2, "selectedCandidateOrdinal": selected,
        "donorObjectives": values[selected], "oldFactoryByJob": previous[0], "newFactoryByJob": [0, 1, 1, 1],
        "expectedResetEvaluations": 5, "previousFactoryAssignments": previous,
        "candidatePopulationIndices": [20, 21, 22], "rankedCandidateOrdinals": [1, 2, 0],
        "candidateObjectives": values, "donorFamily": -1, "particleIndices": [0, 1, 2, 3, 4],
        "clearedPoolRecords": 0, "complete": complete, "successfulResetEvaluations": paid,
        "newObjectives": [[2., 2., 2.] for _ in range(paid)]}
    return [{"type": "context-renewal-summary", **counters}, row], summary


def _reject(rows, summary):
    try:
        validate_observation(rows, summary, "ELITE")
    except ValueError:
        return
    raise AssertionError("Malformed renewal evidence was accepted")


def run_observation_checks():
    rows, summary = fixture()
    assert validate_observation(rows, summary, "ELITE")["deadlineValidSampledCompletedEvents"] == 1
    random_rows, random_summary = fixture("RANDOM")
    assert validate_observation(random_rows, random_summary, "RANDOM")["sampledEvents"][0]["complete"]
    for paid in (0, 3):
        partial, partial_summary = fixture(paid=paid)
        result = validate_observation(partial, partial_summary, "ELITE")
        assert result["deadlineValidSampledCompletedEvents"] == 0 and result["sampledEventsEndedAfterT"] == 1
    wrong = deepcopy(rows)
    wrong[1]["rankedCandidateOrdinals"] = [2, 1, 0]
    _reject(wrong, summary)
    wrong = deepcopy(rows)
    wrong[1]["newFactoryByJob"] = wrong[1]["previousFactoryAssignments"][1]
    _reject(wrong, summary)
    wrong_summary = deepcopy(summary)
    wrong_summary["search"]["context-renewal.personalHistoriesReset"] = 0
    _reject(rows, wrong_summary)
    wrong = deepcopy(rows)
    wrong[1]["endFE"] += 1
    _reject(wrong, summary)
    return {"eliteAndRandomPDDRStableRank": True, "zeroAndPartialPaidResetAccepted": True,
        "lateEventNotDeadlineContribution": True, "oldContextReuseRejected": True,
        "hiddenFEAndHistoryMismatchRejected": True}

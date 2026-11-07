"""Small synthetic checks for genuine complementarity and missing-data gates."""
from copy import deepcopy
from .gate import seed_decision, knowledge_gate
from .protocol import SEEDS
from .replay import request_replay, choose, withdrawals


def record(job, paid, local, whole, *, parent=False):
    return {"objectives": local, "wholeObjectives": whole, "jobs": [job],
        "machines": [0 if parent else 1], "workers": [0], "paidFE": -1 if parent else paid,
        "generation": -1 if parent else 1, "stage": "untracked" if parent else "global",
        "producer": "NONE" if parent else ("MAKESPAN" if paid == 10 else "ENERGY")}


def synthetic_request():
    factories = []
    for factory, paid in enumerate((10, 11)):
        chosen = record(factory, paid, [5., 10., 10.], [5., 100., 100.])
        parent = record(factory, -1, [6., 30., 30.], [6., 60., 60.], parent=True)
        factories.append({"factory": factory, "parent": parent, "records": [chosen], "chosen": deepcopy(chosen)})
    return {"request": 1, "family": 0, "generation": 1, "proposalFE": 20,
        "cycle": 3, "cap": 6., "eta": 0, "energyScale": 1., "wageScale": 1.,
        "parentObjectives": [6., 60., 60.], "outcome": "PROPOSED", "feasible": True,
        "combinedObjectives": [5., 20., 20.], "weightedRelativeImprovement": 2/3,
        "factories": factories}


def check_replay():
    original = synthetic_request(); good = request_replay(original)
    assert good["genuineComplementarity"] and good["distinctChosenPaidFE"] == 2
    elite = deepcopy(original)
    for factory in elite["factories"]:
        for item in [factory["chosen"], *factory["records"]]:
            item["wholeObjectives"] = [5., 20., 20.]
    assert not request_replay(elite)["genuineComplementarity"], "Parent-only gain must not pass"
    absent = deepcopy(original)
    for factory in absent["factories"]:
        for item in [factory["chosen"], *factory["records"]]:
            item["wholeObjectives"][0] = 7.
    result = request_replay(absent)
    assert not result["genuineComplementarity"] and result["bestWholeRelativeGain"] is None
    assert result["feasibilityCompletionWithoutWholeBaseline"]
    first = original["factories"][0]["records"][0]; second = deepcopy(first); second["paidFE"] = 12
    assert choose([first, second], original) is first, "Stable first tie required"
    assert any(not row["withdrawalFeasible"] for row in withdrawals(original))
    future = deepcopy(original); future["factories"][0]["records"][0]["paidFE"] = 21
    try:
        request_replay(future)
    except ValueError:
        pass
    else:
        raise AssertionError("Future/unpaid provenance accepted")
    return {"genuineVsParentAndWhole": True, "copiedEliteRejected": True,
        "missingWholeCannotPass": True, "stableTies": True, "labelWithdrawal": True, "futureSourceRejected": True}


def check_gate():
    counters = {"requests": 10, "tightRequests": 5, "tightRequestsMissingFactory": 1}
    snapshot = request_replay(synthetic_request())
    assert seed_decision("synthetic", SEEDS[0], counters, [snapshot], "synthetic")["passesAllConditions"]
    assert not seed_decision("synthetic", SEEDS[0], None, [snapshot], "synthetic")["passesAllConditions"]
    assert not seed_decision("synthetic", SEEDS[0], counters, None, "synthetic")["passesAllConditions"]
    protocol = {"instances": [{"stem": str(index)} for index in range(6)]}; runs = []
    for index in range(6):
        for number, seed in enumerate(SEEDS):
            runs.append({"instance": str(index), "seed": seed, "variant": "SHARE_SPECIAL", "folder": "synthetic",
                "summary": {"cooperation": {"poolEvidence": counters}},
                "poolReplay": [snapshot] if index < 3 and number < 3 else []})
    assert knowledge_gate(protocol, runs)["gateSatisfied"]
    runs[0]["poolReplay"] = []
    assert knowledge_gate(protocol, runs)["status"] == "SKIPPED_NO_IDENTIFIED_ACTIONABLE_GAP"
    return {"exactThreeInstancesThreeSeeds": True, "missingEvidenceCannotPass": True, "singleLostSeedStopsGate": True}


def run_checks():
    return {"status": "passed", "syntheticReplay": check_replay(), "syntheticGate": check_gate(),
        "optimizerStarted": False, "newSearchFE": 0, "newDecodeFE": 0}

"""Small synthetic routing/signal/cost checks, without optimizer or Decoder."""
from copy import deepcopy
from .observations import target, replay_query, apply_validation_receipt
from .metrics import signal


def synthetic_query():
    return {"type": "demand-local-query", "query": 2, "eligibleQuery": 1,
        "elapsedSeconds": .1, "deadlineValid": True, "family": 0, "physicalGroup": "MAKESPAN",
        "generation": 2, "queryFE": 150, "requestFE": 100, "requestGeneration": 1,
        "cap": 10., "factoryMinC": [9., 12., 12.], "randomFactory": 2,
        "targetFactory": 1, "selectedFactory": 1}


def check_routing():
    assert target([9., 12., 12.], 10.) == 1
    assert target([9., 10., 8.], 10.) == -1
    summary = {"instance": "20_2_3_1.txt", "timeLimitSeconds": 1., "successful": 200,
        "cooperation": {"compositionTiming": {"generationsStarted": 2}}}
    row = synthetic_query()
    assert replay_query(row, "DEMAND", summary, None)["overrodeRandomFactory"]
    sham = deepcopy(row); sham["selectedFactory"] = sham["randomFactory"]
    assert not replay_query(sham, "SHAM", summary, None)["overrodeRandomFactory"]
    future = deepcopy(row); future["requestFE"] = future["queryFE"] + 1
    try:
        replay_query(future, "DEMAND", summary, None)
    except ValueError:
        pass
    else:
        raise AssertionError("Future demand metadata accepted")
    return {"largestPositiveGapAndFirstTie": True, "resolvedNoGap": True,
            "demandOverridesShamPreservesRandom": True, "futureRequestRejected": True}


def check_signal():
    effects = {"SHARE_DEMAND_SPECIAL__vs__SHARE_SHAM_SPECIAL": {
        "T": {"1.5": {"mean_effect_percent": 1., "practical_wins": 3}},
        "FE15000": {"allInstances": {"mean_effect_percent": .1}}},
        "SHARE_DEMAND_SPECIAL__vs__SHARE_SPECIAL": {"T": {"1.5": {"mean_effect_percent": 0., "median_effect_percent": 0.}}}}
    assert signal(effects)["supportedDescriptiveSignal"]
    missing = deepcopy(effects); missing["SHARE_DEMAND_SPECIAL__vs__SHARE_SHAM_SPECIAL"]["FE15000"]["allInstances"]["mean_effect_percent"] = None
    assert not signal(missing)["supportedDescriptiveSignal"]
    negative = deepcopy(effects); negative["SHARE_DEMAND_SPECIAL__vs__SHARE_SPECIAL"]["T"]["1.5"]["median_effect_percent"] = -.01
    assert not signal(negative)["supportedDescriptiveSignal"]
    return {"allFivePredeclaredConditions": True, "missingFECannotPass": True, "negativeOriginalMedianCannotPass": True}


def check_cost():
    run = {"execution": {"controllerValidationSeconds": .2}}
    receipt = {"status": "passed", "extraFE": 0, "additionalControllerValidationSeconds": .03}
    apply_validation_receipt(run, receipt)
    assert abs(run["execution"]["controllerValidationSeconds"] - .23) < 1e-12
    try:
        apply_validation_receipt(run, receipt)
    except ValueError:
        pass
    else:
        raise AssertionError("Demand validation cost added twice")
    return {"additionalValidationIncludedOnce": True}


def run_checks():
    return {"status": "passed", "routing": check_routing(), "signal": check_signal(), "cost": check_cost(),
        "newSearchFE": 0, "newDecodeFE": 0, "optimizerStarted": False}

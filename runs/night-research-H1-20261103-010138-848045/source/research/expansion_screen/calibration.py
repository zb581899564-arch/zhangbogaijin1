"""Bounded, balanced configuration calibration before the main screen."""
import json
import random
import time
import numpy as np
from research.dynamic_benchmark.metrics import hypervolume
from .execution import read, write, run_one


def _final_hv(folder, scale):
    rows = [json.loads(line) for line in (folder/"anytime.jsonl").read_text(encoding="utf-8").splitlines()]
    final = max((r for r in rows if r["checkpointKind"] == "TIME"), key=lambda r:r["checkpoint"])
    if final["elapsedSeconds"] > final["checkpoint"]+1e-9:
        raise ValueError("Calibration future archive")
    points = np.asarray(final["front"]) / np.asarray(scale)
    return hypervolume(points, [1.5]*3)


def _select(root, policy, completed_rounds):
    settings, receipt = {}, []
    selected = policy["clock_and_budget"]["calibration_instances"]
    seeds = policy["clock_and_budget"]["calibration_seeds"]
    instances = {i["stem"]:i for i in policy["instances"]}
    for method in policy["external_comparators"]:
        scores = []
        baseline = {}
        for setting in range(completed_rounds):
            ratios = []
            for stem in selected:
                values = []
                for seed in seeds:
                    folder = root/"calibration"/("setting-"+str(setting))/stem/str(seed)/method
                    values.append(_final_hv(folder, instances[stem]["normalization"]["scale"]))
                value = float(np.mean(values))
                if setting == 0:
                    baseline[stem] = value
                if baseline[stem] <= 1e-12:
                    raise ValueError("Degenerate canonical calibration reference: " + method)
                ratios.append(value / baseline[stem])
            scores.append(float(np.mean(ratios)))
        winner = max(range(completed_rounds), key=lambda setting:(scores[setting], -setting))
        settings[method] = winner
        receipt.append({"method":method, "selectedSetting":winner, "scoresVsCanonical":scores})
    return settings, receipt


def calibrate(root, policy, deadline):
    start = time.monotonic()
    cap = policy["clock_and_budget"]["classic_calibration_wall_cap_seconds"]
    instances = {i["stem"]:i for i in policy["instances"]}
    stems = policy["clock_and_budget"]["calibration_instances"]
    seeds = policy["clock_and_budget"]["calibration_seeds"]
    methods = policy["external_comparators"]
    expected_search = sum(instances[s]["time_seconds"] for s in stems)*len(seeds)*len(methods)
    write(root/"calibration-registration.json", {"settings":{"0":1.0, "1":.5, "2":2.0},
          "meaning":"Only mutationScale varies; all other algorithm rules fixed in compiled source",
          "methods":methods, "instances":stems, "seeds":seeds, "orderSeed":8110009,
          "maximumWallSeconds":cap, "selection":"Mean per-instance HV ratio to that method's canonical setting"}, once=True)
    order_rng = random.Random(8110009)
    estimates, complete = [], 0
    for setting in range(policy["clock_and_budget"]["max_registered_configurations_per_external_method"]):
        reserve = max(expected_search + 16, (max(estimates)*1.1) if estimates else 0)
        if cap-(time.monotonic()-start) < reserve:
            break
        round_start = time.monotonic()
        for stem in stems:
            for seed in seeds:
                order = list(methods)
                order_rng.shuffle(order)
                for method in order:
                    remaining = cap-(time.monotonic()-start)
                    folder = root/"calibration"/("setting-"+str(setting))/stem/str(seed)/method
                    run_one(root, folder, stem, method, seed, instances[stem]["time_seconds"], setting,
                            deadline, extra_cap=remaining)
        estimates.append(time.monotonic()-round_start)
        complete += 1
        write(root/"status.json", {"status":"CALIBRATING", "completedRounds":complete, "completed":0, "expected":policy["runs"]})
        print("CALIBRATION_COMPLETE_ROUND", setting, flush=True)
    if not complete:
        raise RuntimeError("No complete balanced canonical configuration round; screening not ready")
    settings, receipt = _select(root, policy, complete)
    write(root/"selected-settings.json", {"settings":settings, "completedRounds":complete,
          "wallSeconds":time.monotonic()-start, "roundSeconds":estimates, "selection":receipt}, once=True)
    return settings

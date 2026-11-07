"""Execute the frozen sequential screen with one campaign clock and one followup receipt."""
import random
import time
from pathlib import Path
from .analysis import analyze
from .calibration import calibrate
from .decision import evaluate_screen, evaluate_followup
from .execution import prepare, write, run_one
from .report import render


def _jobs(policy, seeds, variants, multiplier=1):
    rng = random.Random(8110007)
    jobs = []
    for instance in policy["instances"]:
        for seed in seeds:
            order = list(variants)
            rng.shuffle(order)
            for variant in order:
                jobs.append({"instance":instance["stem"], "seed":seed, "variant":variant,
                             "seconds":instance["time_seconds"]*multiplier})
    return jobs


def _run_phase(root, policy, settings, deadline, phase, jobs):
    write(root/(phase+"-run-order.json"), jobs, once=True)
    completed = 0
    for job in jobs:
        folder = root/"trials"/phase/job["instance"]/str(job["seed"])/job["variant"]
        run_one(root, folder, job["instance"], job["variant"], job["seed"], job["seconds"],
                settings.get(job["variant"], 0), deadline)
        completed += 1
        write(root/"status.json", {"status":"RUNNING", "phase":phase, "completed":completed,
              "expected":len(jobs), "wallSeconds":deadline.elapsed(),
              "remainingSeconds":deadline.remaining(), "lastRun":str(folder)})
        if completed % len(policy["variants"]) == 0 or completed == len(jobs):
            print("SCREEN_RUNS", phase, completed, "/", len(jobs), job["instance"], flush=True)


def _followup(root, policy, settings, deadline, initial):
    plan = initial.get("followup", {})
    candidate = plan.get("selected_candidate")
    if candidate is None:
        return None
    external = plan["locked_external"]
    # Receipt is written before the first child is dispatched; an interrupted process
    # can never silently obtain a second allowance under the same initial decision.
    deadline.require(policy["followup"]["planned_search_seconds"] + 120)
    write(root/"followup-single-use-receipt.json", {"consumed":True, "candidate":candidate,
          "external":external, "timeMultiplier":2, "seeds":plan["seeds"], "createdEpoch":time.time()}, once=True)
    jobs = _jobs(policy, plan["seeds"], [candidate, "BASELINE", external], 2)
    _run_phase(root, policy, settings, deadline, "followup", jobs)
    deadline.require(10)
    records = analyze(root, policy, phase="followup", candidate=candidate, external=external)
    result = evaluate_followup(records, policy, initial)
    render(root, result, "followup")
    return result


def run(engineering):
    root, policy, deadline = prepare(Path(engineering).resolve())
    print("SCREEN_ROOT", root, flush=True)
    try:
        settings = calibrate(root, policy, deadline)
        write(root/"execution-manifest.json", {"ready":True, "selectedClassicSettings":settings,
              "variants":policy["variants"], "seeds":policy["algorithm_seeds"],
              "primaryReference":policy["metrics"]["primary_reference"],
              "candidateSelection":"SHARE-primary; VALUE_SHARE-secondary; no instance-wise best-of",
              "calibration":"selected-settings.json", "source":"source-manifest.json",
              "engineering":"engineering-acceptance.json"}, once=True)
        jobs = _jobs(policy, policy["algorithm_seeds"], policy["variants"])
        _run_phase(root, policy, settings, deadline, "initial", jobs)
        deadline.require(10)
        records = analyze(root, policy)
        initial = evaluate_screen(records, policy, valid=True)
        render(root, initial)
        print("SCREEN_INITIAL_DECISION", initial["status"], initial.get("ready_for_step6"), flush=True)
        try:
            following = _followup(root, policy, settings, deadline, initial)
        except TimeoutError as error:
            following = {"status":"INSUFFICIENT_EVIDENCE", "ready_for_step6":[], "reason":str(error),
                         "scope":"Incomplete optional followup; complete initial decision remains separately valid"}
            write(root/"followup-cap-result.json", following, once=True)
        ready = sorted(set(initial.get("ready_for_step6", []) + (following or {}).get("ready_for_step6", [])))
        write(root/"status.json", {"status":"SCREEN_COMPLETE", "completed":policy["runs"],
              "expected":policy["runs"], "initialDecision":initial["status"],
              "followupDecision":(following or {}).get("status"), "readyForStep6":ready,
              "wallSeconds":deadline.elapsed(), "remainingSeconds":deadline.remaining()})
        print("SCREEN_COMPLETE", ready, flush=True)
    except Exception as error:
        write(root/"failure.json", {"error":str(error), "type":type(error).__name__,
              "wallSeconds":deadline.elapsed(), "remainingSeconds":deadline.remaining()}, once=True)
        write(root/"status.json", {"status":"INSUFFICIENT_EVIDENCE" if isinstance(error, TimeoutError) else "FAILED_PRESERVED",
              "error":str(error), "wallSeconds":deadline.elapsed(),
              "step6Allowed":False, "partialEvidence":"trials/ and calibration/ preserved"})
        raise
    return root

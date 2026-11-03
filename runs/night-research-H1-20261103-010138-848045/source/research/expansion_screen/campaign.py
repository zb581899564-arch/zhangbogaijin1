"""Execute the frozen sequential screen with one campaign clock and one followup receipt."""
import random
import time
from pathlib import Path
from .analysis import analyze
from .calibration import calibrate
from .decision import evaluate_screen, evaluate_followup
from .execution import prepare, write, read, run_one, CampaignDeadline
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
    order_path = root/(phase+"-run-order.json")
    if order_path.exists():
        if read(order_path) != jobs:
            raise RuntimeError("Refuse changed frozen run order")
    else:
        write(order_path, jobs, once=True)
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


def _execute(root, policy, deadline):
    try:
        selected = root/"selected-settings.json"
        settings = read(selected)["settings"] if selected.exists() else calibrate(root, policy, deadline)
        manifest = {"ready":True, "selectedClassicSettings":settings,
              "variants":policy["variants"], "seeds":policy["algorithm_seeds"],
              "primaryReference":policy["metrics"]["primary_reference"],
              "candidateSelection":"SHARE-primary; VALUE_SHARE-secondary; no instance-wise best-of",
              "calibration":"selected-settings.json", "source":"source-manifest.json",
              "engineering":"engineering-acceptance.json"}
        manifest_path = root/"execution-manifest.json"
        if manifest_path.exists():
            if read(manifest_path) != manifest:
                raise RuntimeError("Refuse changed execution manifest")
        else:
            write(manifest_path, manifest, once=True)
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
        final = {"status":"SCREEN_COMPLETE", "completed":policy["runs"],
              "expected":policy["runs"], "initialDecision":initial["status"],
              "followupDecision":(following or {}).get("status"), "readyForStep6":ready,
              "wallSeconds":deadline.elapsed(), "remainingSeconds":deadline.remaining()}
        write(root/"final-status.json", final, once=True)
        write(root/"status.json", final)
        print("SCREEN_COMPLETE", ready, flush=True)
    except Exception as error:
        failure_path = root/"failure.json"
        if failure_path.exists():
            failure_path = root/("failure-"+str(time.time_ns())+".json")
        write(failure_path, {"error":str(error), "type":type(error).__name__,
              "wallSeconds":deadline.elapsed(), "remainingSeconds":deadline.remaining()}, once=True)
        write(root/"status.json", {"status":"INSUFFICIENT_EVIDENCE" if isinstance(error, TimeoutError) else "FAILED_PRESERVED",
              "error":str(error), "wallSeconds":deadline.elapsed(),
              "step6Allowed":False, "partialEvidence":"trials/ and calibration/ preserved"})
        raise
    return root


def run(engineering):
    root, policy, deadline = prepare(Path(engineering).resolve())
    print("SCREEN_ROOT", root, flush=True)
    return _execute(root, policy, deadline)


def resume(root):
    root = Path(root).resolve()
    deadline = CampaignDeadline(root, read(root/"clock.json")["startedEpoch"])
    deadline.require(30)
    print("SCREEN_RESUME_ORIGINAL_DEADLINE", root, deadline.remaining(), flush=True)
    return _execute(root, read(root/"protocol.json"), deadline)

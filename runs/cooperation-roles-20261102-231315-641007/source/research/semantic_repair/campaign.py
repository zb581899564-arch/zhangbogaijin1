"""Run the two predeclared phases without result-dependent selection."""
from pathlib import Path
import time

from .evidence import prepare, read, status, verify_frozen, write_once
from .execution import CampaignDeadline, analyze_bounded, controller_lock, run_one
from .protocol import PHASES, ROOT, jobs, trial_folder


def _phase(root, protocol, phase, deadline, already_completed):
    order = jobs(protocol, phase)
    order_path = root / (phase + "-run-order.json")
    if order_path.exists():
        if read(order_path) != order:
            raise ValueError("Frozen run order changed")
    else:
        write_once(order_path, order)
    instances = {row["stem"]: row for row in protocol["instances"]}
    summaries = []
    for completed, job in enumerate(order, start=1):
        run, dispatched = run_one(root, trial_folder(root, job), job, instances[job["instance"]],
                                  protocol["variants"][job["variant"]], deadline)
        summaries.append(run["summary"])
        status(root, {"status": "RUNNING", "phase": phase, "phaseCompleted": completed,
                      "phaseExpected": len(order), "completed": already_completed + completed,
                      "expected": protocol["runs"], "wallSeconds": deadline.elapsed(),
                      "remainingSeconds": deadline.remaining(), "lastJob": job,
                      "action": "dispatched" if dispatched else "validated_existing_complete_owner"})
        if completed % len(protocol["phases"][phase]) == 0:
            print("SEMANTIC_RUNS", phase, completed, "/", len(order), job["instance"], flush=True)
    audit = {"status": "passed", "phase": phase, "runs": len(order),
             "genuineFailures": 0, "offlineValidationDecodes": sum(row["offlineValidationDecodes"] for row in summaries),
             "correctnessOnly": True, "qualityUsedForContinuation": False,
             "continuation": "Predeclared cooperation follows valid factorial; SO remains fixed baseline"}
    path = root / (phase + "-correctness.json")
    if path.exists():
        if read(path) != audit:
            raise ValueError("Preserved phase correctness receipt changed")
    else:
        write_once(path, audit)
    return len(order)


def _execute(root):
    with controller_lock(ROOT / "runs", "semantic-repair-controller.lock"), controller_lock(root):
        verify_frozen(root)
        complete = root / "final-status.json"
        if complete.exists():
            final = read(complete)
            if final["status"] != "SEMANTIC_REPAIR_COMPLETE":
                raise ValueError("Unexpected preserved terminal receipt")
            print("SEMANTIC_ALREADY_COMPLETE", root, flush=True)
            return root
        deadline = CampaignDeadline(root)
        protocol = read(root / "protocol.json")
        try:
            deadline.require(30)
            completed = 0
            for phase in PHASES:
                completed += _phase(root, protocol, phase, deadline, completed)
            deadline.require(10)
            output = analyze_bounded(root, deadline)
            deadline.require()
            final = {"status": "SEMANTIC_REPAIR_COMPLETE", "completed": completed,
                     "expected": protocol["runs"], "analysis": str(output.relative_to(root)),
                     "wallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining(),
                     "performanceVerdict": "DESCRIPTIVE_REPAIR_EVIDENCE_ONLY", "step6Allowed": False,
                     "old270DetectorUsed": False, "fixedRepairedBaseline": "SO"}
            write_once(complete, final)
            status(root, final)
            print("SEMANTIC_REPAIR_COMPLETE", root, flush=True)
        except Exception as error:
            failure = {"status": "INSUFFICIENT_EVIDENCE" if isinstance(error, TimeoutError) else "FAILED_PRESERVED",
                       "error": str(error), "type": type(error).__name__, "expected": protocol["runs"],
                       "wallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining(),
                       "step6Allowed": False, "partialEvidence": "All complete and incomplete owners retained; never automatically rerun an incomplete owner"}
            write_once(root / ("failure-" + str(time.time_ns()) + ".json"), failure)
            status(root, failure)
            raise
    return root


def run(engineering):
    root = prepare(engineering)
    print("SEMANTIC_ROOT", root, flush=True)
    return _execute(root)


def resume(root):
    root = Path(root).resolve()
    print("SEMANTIC_RESUME_ORIGINAL_CLOCK", root, flush=True)
    return _execute(root)

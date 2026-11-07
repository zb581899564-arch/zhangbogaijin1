"""Full150 campaign and original-clock resume; no step3 dispatch."""
from pathlib import Path
from research.semantic_repair.evidence import read, write_once, status
from research.semantic_repair.execution import controller_lock
from research.sync_job_audit.execution import Deadline
from .evidence import prepare, verify_frozen
from .execution import run_one, analyze_bounded


def campaign(engineering=None, resume=None):
    root = Path(resume).resolve() if resume else prepare(engineering)
    if (root / "final-status.json").exists():
        raise RuntimeError("Completed campaign cannot restart")
    verify_frozen(root); deadline = Deadline(root); deadline.require()
    protocol = read(root / "protocol.json"); instances = {row["stem"]: row for row in protocol["instances"]}
    print("COOPERATION_ROLES_ROOT", root, flush=True)
    with controller_lock(root):
        try:
            for number, job in enumerate(read(root / "run-order.json"), 1):
                _, dispatched = run_one(root, job, instances[job["instance"]], protocol["variants"][job["variant"]], deadline)
                status(root, {"status": "RUNNING", "completed": number, "expected": 150,
                    "wallSeconds": deadline.elapsed(), "last": job})
                print("COOPERATION_ROLES", number, "/150", job["instance"], job["variant"], "new" if dispatched else "preserved", flush=True)
            output = analyze_bounded(root, deadline); deadline.require()
            gate = read(output / "step3-decision.json")
            final = {"status": "COOPERATION_ROLES_COMPLETE", "completed": 150, "expected": 150,
                "analysis": str(output.relative_to(root)), "wallSeconds": deadline.elapsed(),
                "step3Decision": gate["status"], "step3PerformanceStarted": False,
                "formalStep6Started": False, "automaticFurtherExperiments": False}
            write_once(root / "final-status.json", final); status(root, final)
            print("COOPERATION_ROLES_COMPLETE", output, flush=True)
        except BaseException as error:
            status(root, {"status": "STOPPED_EVIDENCE_PRESERVED", "error": str(error), "wallSeconds": deadline.elapsed()})
            raise
    return root

"""Freeze once; resume only complete owners under the original two deadlines."""
from pathlib import Path

from research.semantic_repair.evidence import read, write_once, status
from research.semantic_repair.execution import controller_lock
from .clock import Deadline
from .evidence import prepare, verify_frozen
from .execution import run_one, analyze_bounded
from .protocol import ROOT


def campaign(engineering=None, config=None, resume=None):
    root = Path(resume).resolve() if resume else prepare(engineering, config)
    if (root / "final-status.json").exists():
        raise RuntimeError("Completed campaign cannot restart")
    deadline = Deadline(root)
    deadline.require()
    verify_frozen(root)
    protocol = read(root / "protocol.json")
    from .observations import require_contracts
    require_contracts(protocol)
    instances = {row["stem"]: row for row in protocol["instances"]}
    print("NIGHT_RESEARCH_ROOT", root, flush=True)
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"), controller_lock(root):
        try:
            for number, job in enumerate(read(root / "run-order.json"), 1):
                _, dispatched = run_one(root, job, instances[job["instance"]], protocol["variants"][job["variant"]], deadline)
                status(root, {"status": "RUNNING", "completed": number, "expected": protocol["runs"],
                    "wallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining(), "last": job})
                print("NIGHT_RESEARCH", number, "/", protocol["runs"], job["instance"], job["variant"],
                    "new" if dispatched else "preserved", flush=True)
            output = analyze_bounded(root, deadline)
            result = {"status": "NIGHT_CAMPAIGN_COMPLETE", "hypothesis": protocol["hypothesis"],
                "completed": protocol["runs"], "expected": protocol["runs"], "wallSeconds": deadline.elapsed(),
                "analysis": str(output.relative_to(root)), "formalStep6Started": False,
                "automaticFollowup": False, "tuningAllowed": False}
            deadline.require()
            write_once(root / "final-status.json", result)
            status(root, result)
        except BaseException as error:
            status(root, {"status": "STOPPED_EVIDENCE_PRESERVED", "error": str(error),
                "wallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining(),
                "classification": "INSUFFICIENT_EVIDENCE", "automaticRetry": False})
            raise
    return root

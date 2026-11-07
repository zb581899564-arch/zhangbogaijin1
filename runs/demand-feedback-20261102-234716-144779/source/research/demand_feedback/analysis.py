"""All90 required: current-campaign metrics, routing evidence and fixed signal."""
from datetime import datetime
import numpy as np
from research.dynamic_benchmark.metrics import nondominated
from research.semantic_repair.analysis import _records, csv_write
from research.semantic_repair.evidence import read, write_once
from .evidence import verify_frozen
from .protocol import jobs
from .observations import load_run
from .metrics import comparisons, signal
from .tables import demand_tables
from .report import write_report


def load_all(root, protocol, deadline):
    instances = {row["stem"]: row for row in protocol["instances"]}; runs = []
    for job in jobs(protocol):
        if deadline:
            deadline.require()
        runs.append(load_run(root, job, instances[job["instance"]], protocol["variants"][job["variant"]]))
    if len(runs) != 90 or len({(r["instance"], r["seed"], r["variant"]) for r in runs}) != 90:
        raise ValueError("All90 unique complete contemporaneous owners required")
    return runs


def audit_runs(runs, deadline):
    audit = {"status": "COMPLETE", "runs": 90, "expected": 90, "genuineFailures": 0,
        "successfulFE": sum(r["summary"]["successful"] for r in runs),
        "attemptedFE": sum(r["summary"]["attempted"] for r in runs),
        "timeInterruptedAttempts": sum(r["summary"]["timeInterruptedAttempts"] for r in runs),
        "returnedSolutionsReplayed": sum(r["summary"]["offlineValidationDecodes"] for r in runs),
        "fixedFEReached": sum(r["fe"] is not None for r in runs),
        "withoutCompletedGeneration": sum(not r["summary"]["search"].get("generations.completed", 0) for r in runs),
        "processWallSeconds": sum(r["execution"]["processWallSeconds"] for r in runs),
        "baseControllerValidationSeconds": sum(r["execution"]["baseControllerValidationSeconds"] for r in runs),
        "demandControllerValidationSeconds": sum(r["execution"]["demandControllerValidationSeconds"] for r in runs),
        "controllerValidationSeconds": sum(r["execution"]["controllerValidationSeconds"] for r in runs),
        "maxOvershootSeconds": max(r["summary"]["deadlineOvershootSeconds"] for r in runs),
        "observerExtraFE": 0, "offlineRoutingReplayExtraFE": 0, "offlinePoolReplayExtraFE": 0,
        "fixedRuleTestedOnce": True, "step3PerformanceStarted": True, "formalStep6Started": False,
        "NSGARuns": 0, "oldNSGAWallScoresUsed": False, "finalHVSourceAttribution": "NOT_IDENTIFIED"}
    if deadline:
        audit.update({"campaignWallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining()})
    return audit


def analyze(root, deadline=None):
    verify_frozen(root); protocol = read(root / "protocol.json"); runs = load_all(root, protocol, deadline)
    references = {}
    for instance in protocol["instances"]:
        if deadline:
            deadline.require()
        stem = instance["stem"]
        references[stem] = nondominated(np.concatenate([r["final"] for r in runs if r["instance"] == stem]))
    records, costs = _records(runs, references, deadline)
    index = {(r["instance"], r["seed"], r["variant"]): r for r in runs}
    for row in costs:
        execution = index[row["instance"], row["seed"], row["variant"]]["execution"]
        row.update({key: execution[key] for key in ("baseControllerValidationSeconds", "demandControllerValidationSeconds")})
    effects = comparisons(records, protocol); descriptive = signal(effects); tables = demand_tables(runs)
    output = root / "analysis" / datetime.now().strftime("analysis-%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False); audit = audit_runs(runs, deadline)
    for stem, front in references.items():
        write_once(output / (stem + "-reference.json"), front.tolist())
    for name, value in (("records", records), ("effects", effects), ("signal", descriptive), ("audit", audit)):
        write_once(output / (name + ".json"), value)
    csv_write(output / "run-metrics.csv", costs)
    for name, rows in tables.items():
        if deadline:
            deadline.require()
        if name == "composition-paid-samples":
            write_once(output / (name + ".json"), rows)
        else:
            csv_write(output / (name + ".csv"), rows)
    write_report(output, effects, descriptive, audit, tables)
    if deadline:
        deadline.require()
    return output

"""Complete150 same-campaign metrics, bounded replay and step3 decision."""
from datetime import datetime
import numpy as np
from research.dynamic_benchmark.metrics import nondominated
from research.semantic_repair.analysis import _records, csv_write
from research.semantic_repair.evidence import read, write_once
from .evidence import verify_frozen
from .protocol import jobs
from .observations import load_run
from .metrics import comparisons, signal
from .gate import knowledge_gate
from .tables import observation_tables
from .report import write_report


def load_all(root, protocol, deadline):
    instances = {row["stem"]: row for row in protocol["instances"]}
    runs = []
    for job in jobs(protocol):
        if deadline:
            deadline.require()
        runs.append(load_run(root, job, instances[job["instance"]], protocol["variants"][job["variant"]]))
    if len(runs) != 150 or len({(r["instance"], r["seed"], r["variant"]) for r in runs}) != 150:
        raise ValueError("All150 complete unique contemporaneous owners required")
    if any(run["execution"] is None for run in runs):
        raise ValueError("Missing owned JVM/validation wall receipts")
    return runs


def audit_runs(runs, deadline):
    result = {"status": "COMPLETE", "runs": len(runs), "expected": 150, "genuineFailures": 0,
        "successfulFE": sum(run["summary"]["successful"] for run in runs),
        "attemptedFE": sum(run["summary"]["attempted"] for run in runs),
        "timeInterruptedAttempts": sum(run["summary"]["timeInterruptedAttempts"] for run in runs),
        "returnedSolutionsReplayed": sum(run["summary"]["offlineValidationDecodes"] for run in runs),
        "fixedFEReached": sum(run["fe"] is not None for run in runs),
        "withoutCompletedGeneration": sum(run["variant"] != "NSGA" and not run["summary"]["search"].get("generations.completed", 0) for run in runs),
        "processWallSeconds": sum(run["execution"]["processWallSeconds"] for run in runs),
        "controllerValidationSeconds": sum(run["execution"]["controllerValidationSeconds"] for run in runs),
        "maxOvershootSeconds": max(run["summary"]["deadlineOvershootSeconds"] for run in runs),
        "observerExtraFE": 0, "offlinePoolReplayExtraFE": 0, "step3PerformanceStarted": False,
        "finalHVSourceAttribution": "NOT_IDENTIFIED", "formalStep6Started": False,
        "coverageScope": "Unreached stages and FE checkpoints remain missing/censored; no re-runs or zero imputation"}
    if deadline:
        result.update({"campaignWallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining()})
    return result


def analyze(root, deadline=None):
    verify_frozen(root)
    protocol = read(root / "protocol.json"); runs = load_all(root, protocol, deadline)
    references = {}
    for instance in protocol["instances"]:
        if deadline:
            deadline.require()
        stem = instance["stem"]
        references[stem] = nondominated(np.concatenate([run["final"] for run in runs if run["instance"] == stem]))
    records, costs = _records(runs, references, deadline)
    effects, interactions = comparisons(records, protocol)
    descriptive = signal(effects, interactions); decision = knowledge_gate(protocol, runs)
    tables = observation_tables(runs)
    output = root / "analysis" / datetime.now().strftime("analysis-%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False)
    for stem, front in references.items():
        write_once(output / (stem + "-reference.json"), front.tolist())
    audit = audit_runs(runs, deadline)
    for name, value in (("effects", effects), ("interaction", interactions), ("signal", descriptive),
                        ("step3-decision", decision), ("audit", audit), ("records", records)):
        write_once(output / (name + ".json"), value)
    csv_write(output / "run-metrics.csv", costs)
    for name, rows in tables.items():
        if deadline:
            deadline.require()
        if name == "composition-paid-samples":
            write_once(output / (name + ".json"), rows)
        else:
            csv_write(output / (name + ".csv"), rows)
    write_report(output, protocol, effects, interactions, descriptive, decision, audit, tables)
    if deadline:
        deadline.require()
    return output

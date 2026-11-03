"""Require the full matrix, then create immutable same-campaign metric artifacts."""
from datetime import datetime
import numpy as np

from research.dynamic_benchmark.metrics import nondominated
from research.semantic_repair.analysis import _records, csv_write
from research.semantic_repair.evidence import read, write_once
from .evidence import verify_frozen
from .protocol import jobs
from .execution import load_run
from .metrics import comparisons
from .interactions import interactions
from .gate import admission
from .report import write_report
from .costs import append_evidence_costs, evidence_totals
from .mechanism_tables import transfer_tables


def load_all(root, protocol, deadline):
    instances = {row["stem"]: row for row in protocol["instances"]}
    runs = []
    for job in jobs(protocol):
        if deadline:
            deadline.require()
        run = load_run(root, job, instances[job["instance"]], protocol["variants"][job["variant"]])
        if run["execution"] is None:
            raise ValueError("Missing complete owned JVM/validation receipt")
        runs.append(run)
    if len(runs) != protocol["runs"] or len({(r["instance"], r["seed"], r["variant"]) for r in runs}) != len(runs):
        raise ValueError("Full unique same-campaign matrix is required")
    return runs


def audit_runs(runs, deadline):
    result = {"status": "COMPLETE", "runs": len(runs), "genuineFailures": 0,
        "successfulFE": sum(r["summary"]["successful"] for r in runs),
        "attemptedFE": sum(r["summary"]["attempted"] for r in runs),
        "timeInterruptedAttempts": sum(r["summary"]["timeInterruptedAttempts"] for r in runs),
        "returnedSolutionsReplayed": sum(r["summary"]["offlineValidationDecodes"] for r in runs),
        "fixedFEReached": sum(r["fe"] is not None for r in runs),
        "processWallSeconds": sum(r["execution"]["processWallSeconds"] for r in runs),
        "controllerValidationSeconds": sum(r["execution"]["controllerValidationSeconds"] for r in runs),
        "maxOvershootSeconds": max(r["summary"]["deadlineOvershootSeconds"] for r in runs),
        "observerExtraFE": 0, "formalStep6Started": False,
        "scope": "All cost retained; unreached FE snapshots censored; no automatic retry or zero imputation"}
    if deadline:
        result.update({"campaignWallSeconds": deadline.elapsed(), "remainingSeconds": deadline.remaining()})
    result.update(evidence_totals(runs))
    return result


def paired_rows(effects):
    rows = []
    for pair, effect in effects.items():
        for point, metric in effect["T"].items():
            for instance in metric["instances"]:
                for seed in instance["paired_seeds"]:
                    rows.append({"comparison": pair, "reference": point, "instance": instance["instance"],
                        "instanceEffectPercent": instance["effect_percent"], "practicalWin": instance["practical_win"],
                        "practicalLoss": instance["practical_loss"], **seed})
    return rows


def analyze(root, deadline=None):
    verify_frozen(root)
    protocol = read(root / "protocol.json")
    runs = load_all(root, protocol, deadline)
    references = {}
    for instance in protocol["instances"]:
        if deadline:
            deadline.require()
        stem = instance["stem"]
        references[stem] = nondominated(np.concatenate([r["final"] for r in runs if r["instance"] == stem]))
    records, costs = _records(runs, references, deadline)
    append_evidence_costs(runs, costs)
    effects, selection = comparisons(records, protocol)
    factorial = interactions(records, protocol)
    decision, audit = admission(protocol, effects, selection), audit_runs(runs, deadline)
    mechanisms = transfer_tables(runs)
    output = root / "analysis" / datetime.now().strftime("analysis-%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False)
    for stem, front in references.items():
        write_once(output / (stem + "-reference.json"), front.tolist())
    for name, value in (("records", records), ("effects", effects), ("classic-selection", selection),
                        ("decision", decision), ("audit", audit), ("interactions", factorial)):
        write_once(output / (name + ".json"), value)
    csv_write(output / "run-metrics.csv", costs)
    csv_write(output / "paired-effects.csv", paired_rows(effects))
    write_once(output / "mechanism-observations.json", [{"instance": r["instance"], "seed": r["seed"],
        "variant": r["variant"], "observation": r["mechanismObservation"]} for r in runs])
    if mechanisms["ownerRows"]:
        write_once(output / "factory-transfer-summary.json", {"methods": mechanisms["methodSummary"], "scope": mechanisms["scope"]})
        csv_write(output / "factory-transfer-owners.csv", mechanisms["ownerRows"])
        csv_write(output / "factory-transfer-opportunities.csv", mechanisms["opportunityRows"])
    write_report(output, protocol, effects, selection, decision, audit, factorial, mechanisms)
    if deadline:
        deadline.require()
    return output

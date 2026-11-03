"""Require a fully replayed genome for every reached checkpoint objective point."""
from collections import Counter
from research.semantic_repair.evidence import read
from research.semantic_repair.trials import json_lines
from .validation import integer, nonnegative, objectives, indices
from .instance_contract import dimensions

POLICY = "SNAPSHOT_GENOMES-v1"
BOUNDARY = "Checkpoint lookup and unique full replay; JSON export remains in process/campaign wall"
PROVENANCE = "Earliest paid admitted objective representative at or before T; no search feedback"


def require_contract(protocol):
    if protocol.get("checkpoint_evidence_schema") != "snapshot-genomes-v1":
        raise ValueError("The frozen checkpoint-genome contract is required")
    if any(spec.get("extra_args") != ["SNAPSHOT_GENOMES"] for spec in protocol["variants"].values()):
        raise ValueError("All methods must enable the identical checkpoint-genome evidence switch")


def _validate_receipt(receipt, summary, checkpoints, genomes):
    if receipt != summary.get("checkpointEvidence"):
        raise ValueError("Checkpoint QA receipt differs from summary.checkpointEvidence")
    required = {"status": "passed", "enabled": True, "policy": POLICY, "allReachedPointsCovered": True,
        "extraSearchFE": 0, "consumesRNG": False, "offlineCostBoundary": BOUNDARY, "provenance": PROVENANCE}
    if any(receipt.get(key) != value for key, value in required.items()):
        raise ValueError("Checkpoint evidence validation, cost or provenance contract differs")
    for key in ("checkpointRows", "reachedCheckpoints", "censoredCheckpoints", "checkpointPoints", "coveredPoints",
                "uniqueOfflineDecodes", "cachedAcceptedObjectiveRepresentatives", "deadlineValidAdmissionEvents",
                "lateAdmissionsExcluded", "extraSearchFE"):
        integer(receipt.get(key), key)
    for key in ("searchCaptureSeconds", "offlineValidationSeconds"):
        nonnegative(receipt.get(key), key)
    reached = [row for row in checkpoints if row.get("reached", True)]
    points = sum(len(row["front"]) for row in reached)
    expected = {"checkpointRows": len(checkpoints), "reachedCheckpoints": len(reached),
        "censoredCheckpoints": len(checkpoints) - len(reached), "checkpointPoints": points, "coveredPoints": len(genomes)}
    if any(receipt[key] != value for key, value in expected.items()) or points != len(genomes):
        raise ValueError("Checkpoint counts do not cover every reached front point exactly")
    unique = len({tuple(row["objectives"]) for row in genomes})
    if receipt["uniqueOfflineDecodes"] != unique:
        raise ValueError("Checkpoint full replay count differs from unique objective representatives")
    cached, admitted = receipt["cachedAcceptedObjectiveRepresentatives"], receipt["deadlineValidAdmissionEvents"]
    if not unique <= cached <= admitted or admitted + receipt["lateAdmissionsExcluded"] > summary["successful"]:
        raise ValueError("Checkpoint cache/admission counters do not close")


def _validate_genome(row, point, summary, jobs, factories):
    objectives(row.get("objectives"), "checkpoint objectives")
    indices(row.get("JS"), "checkpoint JS permutation", jobs, jobs)
    for key in ("FA", "MA", "WA"):
        values = row.get(key)
        if not isinstance(values, list) or len(values) != jobs:
            raise ValueError("Checkpoint four vectors are not aligned")
        for value in values:
            integer(value, "checkpoint " + key, 0, factories - 1 if key == "FA" else None)
    born_fe = integer(row.get("bornFE"), "bornFE", 1, summary["successful"])
    born_seconds = nonnegative(row.get("bornSeconds"), "bornSeconds")
    if row.get("checkpointFE") != point["fe"] or row.get("checkpointElapsedSeconds") != point["elapsedSeconds"]:
        raise ValueError("Checkpoint genome metadata differs from its exact anytime row")
    if born_fe > point["fe"] or born_seconds > point["elapsedSeconds"] or born_seconds > summary["timeLimitSeconds"]:
        raise ValueError("A future or post-deadline genome entered checkpoint evidence")
    if point["checkpointKind"] == "TIME" and born_seconds > point["checkpoint"]:
        raise ValueError("Genome was born after the TIME checkpoint")
    if point["checkpointKind"] == "FE" and born_fe > point["checkpoint"]:
        raise ValueError("Genome was born after the FE checkpoint")


def validate_checkpoint_evidence(folder, checkpoints, summary, instance):
    genomes = json_lines(folder / "checkpoint-solutions.jsonl")
    receipt = read(folder / "checkpoint-validation.json")
    points = {(row["checkpointKind"], row["checkpoint"]): row for row in checkpoints if row.get("reached", True)}
    expected = Counter((kind, value, tuple(obj)) for (kind, value), point in points.items() for obj in point["front"])
    actual, representatives = Counter(), {}
    shape = dimensions(instance["stem"])
    for row in genomes:
        key = row.get("checkpointKind"), row.get("checkpoint")
        if key not in points:
            raise ValueError("Genome row references an unknown or censored checkpoint")
        _validate_genome(row, points[key], summary, shape.jobs, shape.factories)
        objective = tuple(row["objectives"])
        actual[key[0], key[1], objective] += 1
        witness = {field: row[field] for field in ("objectives", "JS", "FA", "MA", "WA", "bornFE", "bornSeconds")}
        if objective in representatives and representatives[objective] != witness:
            raise ValueError("Repeated checkpoint objective changed its earliest admitted representative")
        representatives[objective] = witness
    if actual != expected:
        raise ValueError("Checkpoint objective/genome multiset differs from exact reached fronts")
    _validate_receipt(receipt, summary, checkpoints, genomes)
    return receipt

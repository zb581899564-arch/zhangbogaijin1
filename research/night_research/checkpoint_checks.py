"""Synthetic checkpoint witnesses, including the late-live-archive eviction case."""
from copy import deepcopy
import json
from .checkpoint_evidence import BOUNDARY, PROVENANCE, validate_checkpoint_evidence


def write_fixture(folder, checkpoints, summary):
    genomes = []
    for point in checkpoints:
        if not point.get("reached", True):
            continue
        for objective in point["front"]:
            genomes.append({"checkpointKind": point["checkpointKind"], "checkpoint": point["checkpoint"],
                "objectives": objective, "JS": [0], "FA": [0], "MA": [0], "WA": [0],
                "bornFE": 1, "bornSeconds": .1, "checkpointFE": point["fe"],
                "checkpointElapsedSeconds": point["elapsedSeconds"]})
    unique = len({tuple(row["objectives"]) for row in genomes})
    receipt = {"status": "passed", "enabled": True, "policy": "SNAPSHOT_GENOMES-v1",
        "checkpointRows": len(checkpoints), "reachedCheckpoints": sum(row.get("reached", True) for row in checkpoints),
        "censoredCheckpoints": sum(not row.get("reached", True) for row in checkpoints),
        "checkpointPoints": len(genomes), "coveredPoints": len(genomes), "allReachedPointsCovered": True,
        "uniqueOfflineDecodes": unique, "cachedAcceptedObjectiveRepresentatives": unique,
        "deadlineValidAdmissionEvents": unique, "lateAdmissionsExcluded": 0,
        "searchCaptureSeconds": .01, "offlineValidationSeconds": .02, "extraSearchFE": 0,
        "consumesRNG": False, "offlineCostBoundary": BOUNDARY, "provenance": PROVENANCE}
    summary["checkpointEvidence"] = receipt
    (folder / "checkpoint-validation.json").write_text(json.dumps(receipt), encoding="utf-8")
    write_genomes(folder, genomes)
    return genomes


def write_genomes(folder, rows):
    (folder / "checkpoint-solutions.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def run_checkpoint_checks(folder):
    instance = {"stem": "1_1_1_1"}
    summary = {"successful": 5, "timeLimitSeconds": 2., "archiveSize": 1, "offlineValidationDecodes": 1}
    checkpoints = [{"checkpointKind": "TIME", "checkpoint": 2., "elapsedSeconds": 1.9,
        "fe": 5, "front": [[2., 2., 2.]], "reached": True, "censored": False}]
    genomes = write_fixture(folder, checkpoints, summary)
    assert validate_checkpoint_evidence(folder, checkpoints, summary, instance)["uniqueOfflineDecodes"] == 1
    # Checkpoint proof is independent of the final live archive's objective values.
    summary["finalLiveArchiveObjectives"] = [[1., 1., 1.]]
    assert validate_checkpoint_evidence(folder, checkpoints, summary, instance)["coveredPoints"] == 1
    def rejected(rows):
        write_genomes(folder, rows)
        try:
            validate_checkpoint_evidence(folder, checkpoints, summary, instance)
        except ValueError:
            return
        raise AssertionError("Incomplete/future checkpoint proof was accepted")
    rejected([])
    future = deepcopy(genomes)
    future[0]["bornSeconds"] = 1.95
    rejected(future)
    future = deepcopy(genomes)
    future[0]["bornFE"] = 6
    rejected(future)
    wrong = deepcopy(genomes)
    wrong[0]["objectives"][0] += 1e-12
    rejected(wrong)
    write_genomes(folder, genomes)
    return {"lateLiveArchiveCannotEraseCheckpointWitness": True, "missingGenomeRejected": True,
        "futureBirthRejected": True, "strictObjectiveMismatchRejected": True,
        "checkpointReplaySeparateFromReturnedArchiveQA": True}

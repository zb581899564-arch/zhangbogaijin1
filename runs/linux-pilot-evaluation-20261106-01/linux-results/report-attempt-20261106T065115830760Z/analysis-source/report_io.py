"""Strict read-only pilot inputs and exclusive report output helpers."""
import csv
import json
import platform
import sys
from pathlib import Path


def require_linux():
    if platform.system() != "Linux" or sys.version_info[:2] != (3, 11):
        raise RuntimeError("Pilot statistics and figures require Linux Python 3.11")


def read_json(path):
    return json.loads(Path(path).read_text("utf-8-sig"))


def json_rows(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Malformed JSONL at {path.name}:{number}") from error


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                             if isinstance(value, (list, dict, tuple)) else value
                             for key, value in row.items()})


def identity(run):
    return {key: run[key] for key in ("instance", "seed", "arm")}


def read_receipt(path):
    receipts = list(json_rows(path / "run-receipt.jsonl"))
    if len(receipts) != 1:
        raise ValueError(f"Expected exactly one run receipt: {path}")
    return receipts[0]


def load_runs(root, plan):
    """Load a complete registered batch; never select a favorable subset."""
    expected, runs = set(), []
    for spec in plan["instances"]:
        for seed in plan["seeds"]:
            for arm in plan["arms"]:
                path = root / "science" / spec["stem"] / str(seed) / arm
                expected.add(path / "run-receipt.jsonl")
                receipt = read_receipt(path)
                if receipt["phaseArm"] != arm or receipt["seed"] != seed:
                    raise ValueError("Run identity differs from its registered directory")
                if receipt["error"] is not None or receipt["failed"] != 0:
                    raise ValueError("Failed runs must be retained; complete-batch comparison refused")
                if not receipt["attempted"] == receipt["successful"] == receipt["feLimit"] == plan["fePerRun"]:
                    raise ValueError("Scientific run did not reach the registered common FE endpoint")
                checkpoints = {}
                for row in json_rows(path / "anytime.jsonl"):
                    if row["checkpointKind"] != "FE":
                        continue
                    checkpoint = int(row["checkpoint"])
                    if checkpoint in checkpoints:
                        raise ValueError("Duplicate FE checkpoint")
                    checkpoints[checkpoint] = row
                for checkpoint in plan["checkpoints"]:
                    row = checkpoints.get(checkpoint)
                    if row is None or row.get("reached") is not True or int(row["fe"]) != checkpoint:
                        raise ValueError("Missing registered successful FE checkpoint")
                final = checkpoints[plan["fePerRun"]]["front"]
                if not final:
                    raise ValueError("Empty final front cannot be replaced with a fabricated metric")
                runs.append({"instance": spec["stem"], "seed": seed, "arm": arm,
                             "path": path, "receipt": receipt, "checkpoints": checkpoints,
                             "front": final, "spec": spec})
    if set((root / "science").rglob("run-receipt.jsonl")) != expected:
        raise ValueError("Scientific receipt inventory differs from the registered complete batch")
    if len(runs) != plan["scienceRuns"]:
        raise ValueError("Registered science run count differs")
    return runs


def actual_costs(root):
    """Inventory all retained receipts, including engineering and failures."""
    result = []
    for path in sorted(root.rglob("run-receipt.jsonl")):
        relative = path.relative_to(root)
        if relative.parts[0] not in ("engineering", "engineering-time-limit", "science"):
            continue
        receipt = read_receipt(path.parent)
        qa = path.parent / "checkpoint-validation.json"
        checkpoint_qa = read_json(qa) if qa.exists() else None
        process_path = path.parent / "process.json"
        process = read_json(process_path) if process_path.exists() else {}
        decoder = receipt.get("decoder", {})
        result.append({"source": relative.as_posix(), "scope": relative.parts[0],
                       "phaseArm": receipt.get("phaseArm"), "seed": receipt.get("seed"),
                       **{key: receipt.get(key) for key in ("attempted", "successful", "failed", "searchSeconds", "stopReason", "error")},
                       "physicsQA": receipt.get("physicsQA", {}),
                       **{key: decoder.get(key) for key in ("dynamic.recomputedOperations", "dynamic.reusedOperations", "dynamic.decodeNanos")},
                       "processSeconds": process.get("processSeconds"), "processExitCode": process.get("exitCode"),
                       "checkpointUniqueOfflineDecodes": checkpoint_qa.get("uniqueOfflineDecodes") if checkpoint_qa else None,
                       "checkpointOfflineValidationSeconds": checkpoint_qa.get("offlineValidationSeconds") if checkpoint_qa else None,
                       "cooperationSubsystemSecondsIncludesCommonLifecycle": receipt.get("search", {}).get("cooperation", {}).get("cooperationSeconds"),
                       "checkpointQA": checkpoint_qa})
    return result

"""Frozen paid snapshots and outcome-independent sampling for a complete-schedule relay probe."""
from collections import Counter
from hashlib import sha256
from pathlib import Path

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, nondominated
from reverse_ledger_analysis import archive_admissions

ANCHOR = ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093"
CAPTURES = ROOT / "runs/center-entry-cross-20261103-233434-666587/reused-captures.json"
ROLES = ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")
SIZES = (15, 55, 15, 15)
STEPS, SAMPLE, REPS = 256, 8, (9173001, 9173027)


def inputs():
    snapshots, origins, references = [], {}, []
    for cohort, folder in read(CAPTURES).items():
        entry, = rows(Path(folder) / "entry.jsonl")
        assert len(entry["reference"]) == 100 and max(x["paid"] for x in entry["reference"]) <= 5100
        origins[cohort] = {"path": str(Path(folder) / "entry.jsonl"),
                           "SHA256": sha256((Path(folder) / "entry.jsonl").read_bytes()).hexdigest()}
        references.extend(entry["reference"])
        start = 0
        for role, size in zip(ROLES, SIZES):
            free = [(start + i, r) for i, r in enumerate(entry["reference"][start:start + size]) if r["family"] is None]
            assert len(free) == (47 if role == "CENTER" else 11)
            chosen = np.rint(np.linspace(0, len(free) - 1, SAMPLE)).astype(int)
            assert len(set(chosen)) == SAMPLE
            for rank, ix in enumerate(chosen):
                index, record = free[ix]
                snapshots.append({"id": f"{cohort}-{index}", "cohort": cohort, "index": index, "source": role,
                                  "split": "TRAIN" if rank % 2 == 0 else "HOLDOUT", **record})
            start += size
    background = []
    for label in ("SPECIAL", "UNIFORM"):
        mode = "SHARE_JOB_ALIGNED" + ("_UNIFORM" if label == "UNIFORM" else "")
        path = ANCHOR / label / "trials/fatigue" / mode
        background.extend(p for t, p in archive_admissions(path) if t <= 5100)
    background.extend(x["objectives"] for x in references)
    front = nondominated(background).tolist()
    assert len(snapshots) == 64
    assert Counter(x["split"] for x in snapshots) == {"TRAIN": 32, "HOLDOUT": 32}
    return snapshots, references, front, origins


def cases(snapshots):
    result = []
    for rep, seed in enumerate(REPS):
        for i, parent in enumerate(snapshots):
            for k in range(4):
                target = ROLES[(k + i + rep) % 4]
                result.append({"id": f"{parent['id']}:{target}:{rep}", "parent": parent["id"],
                               "target": target, "seed": seed, "continuationFE": STEPS})
    assert len(result) == 512
    return result


def encoded(record):
    return [",".join(map(str, record["objectives"]))] + [
        ",".join(map(str, record["genome"][k])) for k in ("JS", "FA", "MA", "WA")]

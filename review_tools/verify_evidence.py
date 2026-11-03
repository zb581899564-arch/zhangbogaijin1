"""Check the curated file manifest and recompute key fixed-FE results from saved evidence."""
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.dynamic_benchmark.metrics import hypervolume, nondominated


TRIALS = "trials/fatigue"
ROLE_RUN = ROOT / "runs/dynamic-deep-roles-20261103-212007-121034"
DEEP_RUN = ROOT / "runs/dynamic-deep-local-20261103-184901-271850"
CURRENT, SHARE, NSGA = "current-share", "deep-share", "deep-nsga"
SHARE_MODE, UNIFORM_MODE, NSGA_MODE = "SHARE_JOB_ALIGNED", "SHARE_JOB_ALIGNED_UNIFORM", "NSGA2_4V"
STAGES = ("initialization", "global", "inter", "intra")
FIXED_FE = 500_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def pointset(points):
    return {tuple(p) for p in points}


def verify_manifest():
    manifest = load(ROOT / "MANIFEST.json")
    for name, record in manifest["files"].items():
        path = ROOT / name
        require(path.is_file() and not path.is_symlink() and ROOT in path.resolve().parents, name)
        data = path.read_bytes()
        require(len(data) == record["bytes"] and sha256(data).hexdigest() == record["sha256"], name)
    require(len(manifest["files"]) == manifest["summary"]["files"], "Manifest count")
    print(f"MANIFEST_OK {len(manifest['files'])} files")


def check_trial(folder):
    receipt, = jsonl(folder / "run-receipt.jsonl")
    require(receipt["attempted"] == receipt["successful"] == FIXED_FE and receipt["failed"] == 0
            and receipt["stopReason"] == "FE_LIMIT" and receipt["seed"] == 8111009, str(folder))
    dec = receipt["decoder"]
    require(dec["dynamic.evaluations"] == FIXED_FE
            and dec["dynamic.reusedOperations"] + dec["dynamic.recomputedOperations"] == 40 * FIXED_FE, str(folder))
    paid = tuple(receipt["search"][s + ".evaluations"] for s in STAGES)
    require(sum(paid) == FIXED_FE, str(folder))
    curve = {row["fe"]: row["front"] for row in jsonl(folder / "anytime.jsonl") if row["reached"]}
    solutions = jsonl(folder / "solutions.jsonl")
    require(pointset(curve[FIXED_FE]) == pointset(row["objectives"] for row in solutions), str(folder))
    initial = (folder / "initial-population.jsonl").read_bytes()
    require(len(initial.splitlines()) == 100, str(folder))
    slots = None
    if (folder / "local-ledger.csv").exists():
        keys = ("visit", "group", "round", "factory", "paid")
        slots = [tuple(int(r[k]) for k in keys) for r in csv_rows(folder / "local-ledger.csv")]
        require(len(slots) == 3551 and slots[-1][0] == 115, str(folder))
        require(paid == (100, 10_000, 586, 489_314), str(folder))
        require(sum(x[4] for x in slots if x[2] < 0) == paid[2]
                and sum(x[4] for x in slots if x[2] >= 0) == paid[3], str(folder))
    if (folder / "archive-admissions.csv").exists():
        admitted = [(int(r["fe"]), [float(r[k]) for k in ("cmax", "tec", "twc")])
                    for r in csv_rows(folder / "archive-admissions.csv")]
        for fe, front in curve.items():
            replay = nondominated([p for paid_fe, p in admitted if paid_fe <= fe])
            require(pointset(replay) == pointset(front), f"{folder}: archive at FE={fe}")
    return initial, slots, curve


def check_hv(run, trials):
    protocol = load(run / "protocol.json")
    lower = np.asarray(protocol["normalization"]["lower"])
    scale = np.asarray(protocol["normalization"]["scale"])
    for row in load(run / "comparison.json"):
        fe = row["FE"]
        for label, (_, _, curve) in trials.items():
            normed = (np.asarray(curve[fe]) - lower) / scale
            actual = hypervolume(normed, (1.5, 1.5, 1.5))
            expected = row["arms"][label]["HV"]["1.5"]
            require(math.isclose(actual, expected, abs_tol=1e-12, rel_tol=0), f"{label} HV at {fe}")
            if fe in (250_000, FIXED_FE):
                print(f"{label} FE={fe} HV={actual:.9f}")


def main():
    verify_manifest()
    deep = {label: check_trial(DEEP_RUN / label / TRIALS / mode)
            for label, mode in ((CURRENT, SHARE_MODE), (SHARE, SHARE_MODE), (NSGA, NSGA_MODE))}
    roles = {label: check_trial(ROLE_RUN / label / TRIALS / mode)
             for label, mode in (("SPECIAL", SHARE_MODE), ("UNIFORM", UNIFORM_MODE))}
    for name, (initial, slots, _) in {**deep, **roles}.items():
        require(initial == deep[SHARE][0] and (name == CURRENT or slots == deep[SHARE][1]), name)
    for fe, front in deep[SHARE][2].items():
        require(pointset(front) == pointset(roles["SPECIAL"][2][fe]), f"SPECIAL replay at {fe}")
    check_hv(DEEP_RUN, deep)
    check_hv(ROLE_RUN, roles)
    print("CORE_EVIDENCE_OK 5 accepted 500000-FE runs; fixed initial genomes, local quotas and saved fronts")


if __name__ == "__main__":
    main()

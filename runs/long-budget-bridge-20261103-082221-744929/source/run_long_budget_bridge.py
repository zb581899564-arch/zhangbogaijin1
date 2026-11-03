"""Single-seed, fixed 500000-FE diagnostic; reuse frozen algorithms without tuning."""
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.dynamic_benchmark.metrics import hypervolume, igd_plus, nondominated
from research.night_research.evidence import verify_frozen
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.execution import controller_lock
from baseline_build import execute

FROZEN = ROOT / "runs/night-research-H1-20261103-010138-848045"
STEM, SEED = "20_2_3_1", 8111009
FE = (100, 15000, 50000, 100000, 250000, 500000)
PAIR = ("NSGA2_4V", "BASELINE")
DESIGN = {
    "static": PAIR,
    "append_beta0": PAIR[::-1],
    "fatigue": ("NSGA2_4V", "BASELINE", "SHARE_JOB_ALIGNED"),
}
SOURCES = (
    ROOT / "src/java/dynamicentries/LongBudgetRun.java",
    ROOT / "src/java/normalized/RunOutput.java",
)


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prepare(root):
    verify_frozen(FROZEN)
    normalization = next(row["normalization"] for row in read(FROZEN / "protocol.json")["instances"]
                         if row["stem"] == STEM)
    write_once(root / "protocol.json", {
        "instance": STEM, "seed": SEED, "seedRule": "First registered H1 seed; not quality-selected",
        "budget": FE[-1], "checkpoints": list(FE), "designAndOrder": DESIGN,
        "frozenSource": str(FROZEN), "normalization": normalization, "standby": 1,
        "algorithmScope": "Frozen SO QGS, setting-0 NSGA2_4V and frozen SO SHARE_JOB_ALIGNED",
        "staticScope": "Reconstructed canonical-v1, not author binary or original-data reproduction",
        "reference": "Within each condition, ND union of its completed 500000-FE fronts for empirical IGD+",
        "scope": "Exploratory single instance and seed; no tuning, original-paper NSGA port or expansion decision",
    })
    inputs = root / "inputs"
    shutil.copytree(FROZEN / "inputs" / STEM, inputs)
    strong = (inputs / "fatigue-input.txt").read_text(encoding="utf-8").splitlines()
    beta0 = ["# source=Frozen strong_fast with only beta set to zero"]
    for line in strong[1:]:
        if line.strip():
            cells = line.split(",")
            assert len(cells) == 7
            cells[5] = "0.0"
            beta0.append(",".join(cells))
    (inputs / "fatigue-beta0.txt").write_text("\n".join(beta0) + "\n", encoding="utf-8")
    classes = root / "classes"
    classes.mkdir()
    source_dir = root / "source"
    source_dir.mkdir()
    copies = [shutil.copy2(path, source_dir / path.name) for path in SOURCES]
    shutil.copy2(Path(__file__), source_dir / Path(__file__).name)
    base = (FROZEN / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base,
             "-d", str(classes), *map(str, copies)], root / "compile.log")
    cp = str(classes) + ";" + base
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    return cp, normalization


def run_one(root, cp, condition, mode, checkpoints, engineering=False):
    folder = root / ("engineering" if engineering else "trials") / condition / mode
    folder.mkdir(parents=True)
    inputs = root / "inputs"
    fatigue = {"static": "STATIC", "append_beta0": str(inputs / "fatigue-beta0.txt"),
               "fatigue": str(inputs / "fatigue-input.txt")}[condition]
    cmd = ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "research.dynamic.LongBudgetRun",
           str(inputs / (STEM + ".txt")), str(inputs / "RECONSTRUCTED-setup.txt"), fatigue,
           str(folder), mode, str(checkpoints[-1]), str(SEED), *map(str, checkpoints)]
    write_once(folder / "command.json", cmd)
    print("START", condition, mode, checkpoints[-1], flush=True)
    started = time.monotonic()
    code = None
    try:
        with (folder / "run.log").open("x", encoding="utf-8") as stream:
            code = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=600).returncode
    finally:
        write_once(folder / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - started})
    if code != 0:
        raise RuntimeError(f"{folder}: {(folder / 'run.log').read_text(encoding='utf-8', errors='replace')[-3000:]}")
    receipt, = rows(folder / "run-receipt.jsonl")
    summary = read(folder / "summary.json")
    curve = rows(folder / "anytime.jsonl")
    solutions = rows(folder / "solutions.jsonl")
    assert receipt["seed"] == SEED and receipt["mode"] == mode and receipt["stopReason"] == "FE_LIMIT"
    assert receipt["successful"] == receipt["attempted"] == checkpoints[-1] and receipt["failed"] == 0
    assert [row["checkpoint"] for row in curve] == list(checkpoints)
    assert all(row["reached"] and row["fe"] == row["checkpoint"] and row["front"] for row in curve)
    assert all(np.isfinite(row["front"]).all() for row in curve)
    assert len(solutions) == summary["archiveSize"] == summary["offlineValidationDecodes"]
    assert objectives(curve[-1]["front"]) == objectives(row["objectives"] for row in solutions)
    print("PASS", condition, mode, f"{receipt['searchSeconds']:.2f}s", len(solutions), flush=True)
    return {"receipt": receipt, "curve": curve, "replays": len(solutions)}


def objectives(front):
    return {tuple(point) for point in front}


def check_frozen_trace(results):
    for mode, label in (("NSGA2_4V", "NSGA2_4V"), ("SHARE_JOB_ALIGNED", "SHARE_STATIC")):
        folder = FROZEN / "trials/H1" / STEM / str(SEED) / label
        old, = [row for row in rows(folder / "anytime.jsonl") if row["checkpointKind"] == "FE"]
        new = results["fatigue"][mode]["curve"][FE.index(15000)]
        if not old["reached"] or objectives(old["front"]) != objectives(new["front"]):
            raise ValueError(f"Frozen {mode} 15000-FE archive does not match")


def c_coverage(front, other):
    a, b = np.asarray(front), np.asarray(other)
    return float(np.any(np.all(a[:, None, :] <= b[None, :, :], axis=2), axis=0).mean())


def analyze(root, results, norm):
    scale = np.asarray(norm["scale"])
    out = {}
    for condition, methods in results.items():
        control = methods["NSGA2_4V"]["curve"]
        reference = nondominated(np.concatenate([np.asarray(run["curve"][-1]["front"]) / scale
                                                  for run in methods.values()]))
        out[condition] = {}
        for mode, run in methods.items():
            report = []
            for row, comparison in zip(run["curve"], control):
                front, base = np.asarray(row["front"]) / scale, np.asarray(comparison["front"]) / scale
                hv = float(hypervolume(front, (1.5,) * 3))
                baseline = float(hypervolume(base, (1.5,) * 3))
                report.append({"FE": row["fe"], "seconds": row["elapsedSeconds"], "HV": hv,
                               "vsNSGA_pct": 100 * (hv / baseline - 1), "IGDplus": float(igd_plus(front, reference)),
                               "HV_sensitivity": {str(ref): 100 * (hypervolume(front, (ref,) * 3)
                                   / hypervolume(base, (ref,) * 3) - 1) for ref in (1.25, 2.0)},
                               "C_covers_NSGA": c_coverage(front, base), "C_NSGA_covers": c_coverage(base, front),
                               "objectiveMin": np.min(row["front"], axis=0).tolist(),
                               "frontSize": len(front)})
            out[condition][mode] = {"curve": report, "archiveFullReplays": run["replays"],
                                    "searchSeconds": run["receipt"]["searchSeconds"]}
    write_once(root / "comparison.json", out)


def main():
    root = ROOT / "runs" / datetime.now().strftime("long-budget-bridge-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("BRIDGE_ROOT", root, flush=True)
    start = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            cp, norm = prepare(root)
            smoke = [run_one(root, cp, "static", mode, (100, 1000), engineering=True) for mode in PAIR]
            assert objectives(smoke[0]["curve"][0]["front"]) == objectives(smoke[1]["curve"][0]["front"])
            results = {condition: {mode: run_one(root, cp, condition, mode, FE) for mode in modes}
                       for condition, modes in DESIGN.items()}
            for methods in results.values():
                assert objectives(methods["BASELINE"]["curve"][0]["front"]) == objectives(
                    methods["NSGA2_4V"]["curve"][0]["front"])
            check_frozen_trace(results)
            analyze(root, results, norm)
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(error),
                                         "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "runs": 7, "successfulFE": 3500000,
                                     "engineeringFE": 2000, "frozen15000ArchivesExact": True,
                                     "wallSeconds": time.monotonic() - start})
    print("BRIDGE_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()

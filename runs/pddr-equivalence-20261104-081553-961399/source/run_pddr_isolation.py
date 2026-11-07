"""Audit a linear local PDDR kernel, then compare fixed-FE and clock-cut performance."""
from datetime import datetime
from hashlib import sha256
import math
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from reverse_ledger_analysis import archive_admissions
from run_dynamic_deep_roles import BRIDGE, ledger
from run_dynamic_reverse_ledger_audit import MODES, POINTS, ROOT, SEED, STEM, trial_folder
from run_long_budget_bridge import controller_lock, execute, hypervolume, objectives, read, rows, write_once
from run_paired_qgs_guidance import replace


ANCHOR = ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093"
ROLE = ROOT / "runs/dynamic-deep-roles-20261103-212007-121034"
ORDER = (("SPECIAL", "LEGACY"), ("NSGA", "LINEAR"), ("SPECIAL", "LINEAR"), ("NSGA", "LEGACY"))
TIME = (1, 2, 4, 6, 8, 10, 12)
STAGES = ("initialization", "global", "inter", "intra")


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir()
    classes.mkdir()
    base = (ROLE / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    body = (ANCHOR / "source/LocalSearch.java").read_text(encoding="utf-8")
    assert body.count("ReverseAudit.run().better(") == 3
    local = source / "LocalSearch.java"
    local.write_text(body.replace("ReverseAudit.run().better(", "LocalPddrKernel.better("), encoding="utf-8")
    files = [local, shutil.copy2(ANCHOR / "source/SearchState.java", source)]
    for name in ("LocalPddrKernel", "PddrPaidDigest", "PddrIsolationRun"):
        files.append(shutil.copy2(ROOT / f"src/algorithms/diagnostics/{name}.java", source))
    shutil.copy2(Path(__file__), source)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base, "-d", str(classes),
             *map(str, files)], root / "compile.log")
    cp = f"{classes};{base}"
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    execute(["java", "-cp", cp, "org.uma.jmetal.util.research.runtime.AnytimeChecks"], root / "anytime-checks.log")
    write_once(root / "class-hashes.json", {p.relative_to(classes).as_posix(): sha256(p.read_bytes()).hexdigest()
                                          for p in classes.rglob("*.class")})
    return cp


def run(root, cp, algorithm, kernel):
    path = root / f"{algorithm}-{kernel}"
    path.mkdir()
    inputs = root / "inputs"
    cmd = ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "research.dynamic.PddrIsolationRun",
           str(inputs / f"{STEM}.txt"), str(inputs / "RECONSTRUCTED-setup.txt"), str(inputs / "fatigue-input.txt"),
           str(path), MODES[algorithm], kernel, str(root / "ledger.csv"), str(POINTS[-1]), str(SEED), *map(str, POINTS)]
    write_once(path / "command.json", cmd)
    print("PDDR", algorithm, kernel, flush=True)
    start, code = time.monotonic(), None
    try:
        with (path / "run.log").open("x", encoding="utf-8") as log:
            code = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300).returncode
    finally:
        write_once(path / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - start})
    if code:
        raise RuntimeError((path / "run.log").read_text(encoding="utf-8", errors="replace")[-3000:])
    return path


def check_arm(root, path, label, kernel):
    prior = trial_folder(ANCHOR, label)
    accepted = read(ANCHOR / f"validation-{label}.json")
    receipt, = rows(path / "run-receipt.jsonl")
    assert receipt["attempted"] == receipt["successful"] == receipt["decoder"]["dynamic.evaluations"] == POINTS[-1]
    assert receipt["failed"] == 0 and receipt["stopReason"] == "FE_LIMIT" and receipt["seed"] == SEED
    assert {s: receipt["search"].get(s + ".evaluations", 0) for s in STAGES} == accepted["stage"]
    assert ledger(path) == ledger(prior), (label, kernel, "ledger and continuation trace")
    assert (path / "initial-population.jsonl").read_bytes() == (prior / "initial-population.jsonl").read_bytes()
    assert (path / "solutions.jsonl").read_bytes() == (prior / "solutions.jsonl").read_bytes()
    curve, old = (rows(p / "anytime.jsonl") for p in (path, prior))
    assert [r["fe"] for r in curve] == list(POINTS)
    assert all(r["reached"] and objectives(r["front"]) == objectives(a["front"]) for r, a in zip(curve, old))
    assert objectives(curve[-1]["front"]) == objectives(r["objectives"] for r in rows(path / "solutions.jsonl"))
    stats = receipt["pddr"]
    assert stats["mode"] == kernel and stats["scoreAndDecisionMismatches"] == 0
    if kernel == "AUDIT":
        assert receipt["paidSHA256"] == accepted["obs"]["paidSHA256"]
        assert archive_admissions(path) == archive_admissions(prior)
        assert stats["auditedCenterComparisons"] == accepted["obs"]["pddrComparisons"] > 0
        assert stats["auditedTies"] == accepted["obs"]["pddrTies"]
    else:
        assert receipt["paidSHA256"] is None and stats["auditedCenterComparisons"] == 0
        timed = rows(path / "time.jsonl")
        assert len(timed) == len(TIME) and all(r["reached"] and r["front"] for r in timed)
        assert all(r["checkpointKind"] == "TIME" and math.isclose(r["checkpoint"], t)
                   and r["elapsedSeconds"] <= t + 1e-9 for r, t in zip(timed, TIME))
        assert [r["fe"] for r in timed] == sorted(r["fe"] for r in timed)
        for r, t in zip(timed, TIME):
            if receipt["searchSeconds"] <= t:
                assert r["fe"] == POINTS[-1] and objectives(r["front"]) == objectives(curve[-1]["front"])
    summary = read(path / "summary.json")
    assert summary["offlineValidationDecodes"] == len(rows(path / "solutions.jsonl"))
    report = {"label": label, "kernel": kernel, "fe": receipt["successful"], "pddr": stats,
              "searchSeconds": receipt["searchSeconds"], "wallSeconds": read(path / "process.json")["wallSeconds"],
              "offlineValidationDecodes": summary["offlineValidationDecodes"], "paidSHA256": receipt["paidSHA256"]}
    write_once(root / f"verified-{label}-{kernel}.json", report)
    return report


def compare(root, reports):
    norm = read(ANCHOR / "protocol.json")["normalization"]
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    hv = lambda r: float(hypervolume((np.asarray(r["front"]) - lower) / scale, (1.5,) * 3))
    names = [f"{a}-{k}" for a, k in ORDER]
    by_fe = {name: rows(root / name / "anytime.jsonl") for name in names}
    by_time = {name: rows(root / name / "time.jsonl") for name in names}
    speed = {a: reports[f"{a}-LEGACY"]["searchSeconds"] / reports[f"{a}-LINEAR"]["searchSeconds"]
             for a in ("SPECIAL", "NSGA")}
    timed = [{"seconds": t, "arms": {k: {"fe": by_time[k][i]["fe"], "hv": hv(by_time[k][i]),
                                          "observedAt": by_time[k][i]["elapsedSeconds"]} for k in names}}
             for i, t in enumerate(TIME)]
    return {"HVReference": [1.5] * 3, "searchSpeedup": speed,
            "fixedFE": [{"fe": f, "arms": {k: hv(by_fe[k][i]) for k in names}} for i, f in enumerate(POINTS)],
            "fixedTimeWith500kCap": timed, "timingReports": reports}


def main():
    root = ROOT / "runs" / datetime.now().strftime("pddr-equivalence-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("PDDR_ROOT", root, flush=True)
    t, complete = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            assert read(ANCHOR / "analysis-status.json")["status"] == "COMPLETE"
            frozen = trial_folder(ANCHOR, "U_RECORD") / "local-ledger.csv"
            shutil.copy2(frozen, root / "ledger.csv")
            shutil.copytree(BRIDGE / "inputs", root / "inputs")
            write_once(root / "protocol.json", {"instance": STEM, "seed": SEED, "searchFECap": POINTS[-1],
                "ledger": str(frozen), "ledgerSHA256": sha256(frozen.read_bytes()).hexdigest(),
                "auditOrder": ["SPECIAL", "NSGA"], "timingOrder": list(ORDER), "timeCutsSeconds": list(TIME),
                "scope": "Only local CENTER pair comparison changes. No global or boundary preference changes.",
                "timePolicy": "One sequential JVM per cell, no score/trajectory audits during timing. "
                              "Search capped at 500k FE; use the most recent completed archive at each common time cut.",
                "acceptance": "Legacy-vs-linear scores bitwise and decisions equal on every audited local CENTER comparison; "
                              "original paid trace SHA, initialization, slot continuations, checkpoints and final genomes all match."})
            cp = build(root)
            for algorithm in ("SPECIAL", "NSGA"):
                path = run(root, cp, algorithm, "AUDIT")
                check_arm(root, path, algorithm, "AUDIT")
                complete.append(f"{algorithm}-AUDIT")
            write_once(root / "equivalence-gate.json", {"status": "PASS", "audited": list(complete)})
            reports = {}
            for algorithm, kernel in ORDER:
                path = run(root, cp, algorithm, kernel)
                reports[path.name] = check_arm(root, path, algorithm, kernel)
                complete.append(path.name)
            write_once(root / "comparison.json", compare(root, reports))
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": complete, "error": str(error)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": complete, "auditFE": 1000000,
                                     "timingFE": 2000000, "wallSeconds": time.monotonic() - t})
    print("PDDR_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()

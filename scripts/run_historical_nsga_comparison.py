"""Audit the supplied NSGA-II counter, then compare three static methods at 500000 actual FE."""
from datetime import datetime
import difflib
from pathlib import Path
import re
import shutil
import subprocess
import time

from run_long_budget_bridge import (
    FROZEN, ROOT, SEED, STEM, analyze, controller_lock, execute, objectives, prepare,
    read, rows, run_one, verify_frozen, write_once,
)

ORIGINAL = ROOT.parent / "李明哲-毕业材料/5.第四章代码/jMetal-jmetal-DHHFSP"
BRIDGE = ROOT / "runs/long-budget-bridge-20261103-082221-744929"
LEGACY = "NSGA2_HISTORICAL_ADAPTED"
POINTS = (100, 1000, 15000, 50000, 100000, 250000, 500000)
OLD_SOURCES = (
    "jmetal-algorithm/src/main/java/org/uma/jmetal/algorithm/multiobjective/nsgaii/NSGAII.java",
    "jmetal-core/src/main/java/org/uma/jmetal/operator/impl/crossover/PMXCrossover.java",
    "jmetal-core/src/main/java/org/uma/jmetal/operator/impl/mutation/PermutationSwapMutation.java",
)


def adapt_nsga(source):
    start = "        double object1 = Double.MAX_VALUE;"
    end = "        RankingAndCrowdingSelection<S> rankingAndCrowdingSelection;"
    assert source.count(start) == source.count(end) == 1
    left, right = source.index(start), source.index(end)
    block = source[left:right]
    assert "getObjective(6)" in block and "System.out.println" in block
    source = source[:left] + source[right:]
    # Preserve the old stochastic branches, with all draws on the same recorded stream.
    source, count = re.subn(r"^(?!\s*//)([^\n]*?)\bnew Random\(\)", r"\1org.uma.jmetal.util.research.runtime.SeededRandom.current()",
                           source, flags=re.M)
    assert count == 8, f"Unexpected old RNG call sites: {count}"
    return source


def prepare_legacy(root):
    verify_frozen(FROZEN)
    assert read(BRIDGE / "status.json")["status"] == "COMPLETE"
    assert read(BRIDGE / "protocol.json")["seed"] == SEED
    shutil.copytree(BRIDGE / "inputs", root / "inputs")
    write_once(root / "protocol.json", {
        "instance": STEM, "seed": SEED, "model": "canonical-v1 static insertion and right-shift",
        "setupAndStandby": "Same reconstructed SUT and standby=1.0 as completed 500k bridge",
        "referenceBridge": str(BRIDGE), "probeNominalFE": 5000,
        "actualFE": POINTS[-1], "checkpoints": list(POINTS),
        "order": [LEGACY, "BASELINE", "NSGA2_4V"],
        "historical": {"implementation": "Supplied snapshot NSGAII, PMX and swap; not the certified paper executable",
                       "population": 100, "PMX": .4, "JSswap": .2, "FAcross": .2, "FAmut": .04,
                       "WAcross": .3, "MAcross": .4, "WAmut": .1, "MAmut": .15,
                       "rates": "As passed by the supplied ALLAlgorithmRun to lc_psode/NSGAIIRun",
                       "adaptations": ["common decoder, deterministic repair and seeded initialization",
                                       "redirect active local Random constructors to shared seeded stream",
                                       "remove legacy debug print reading objective index 6",
                                       "count calls independently at decoder entry; exact stop only in performance arm",
                                       "common external paid archive; legacy reproduction and replacement preserved"]},
    })
    sources = root / "source"
    sources.mkdir()
    exact, adapted, classes = sources / "original", sources / "adapted", root / "classes"
    for folder in (exact, adapted, classes):
        folder.mkdir()
    compile_files = []
    for relative in OLD_SOURCES:
        source = ORIGINAL / relative
        shutil.copy2(source, exact / source.name)
        target = adapted / source.name
        if source.name == "NSGAII.java":
            old = source.read_text(encoding="utf-8-sig")
            new = adapt_nsga(old)
            target.write_text(new, encoding="utf-8")
            (sources / "NSGAII-adaptation.diff").write_text("".join(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True), fromfile="supplied", tofile="adapted")), encoding="utf-8")
        else:
            shutil.copy2(source, target)
        compile_files.append(str(target))
    for source in (ROOT / "src/algorithms/historical/HistoricalNsgaRun.java", Path(__file__)):
        dest = adapted / source.name
        shutil.copy2(source, dest)
        if dest.suffix == ".java":
            compile_files.append(str(dest))
    cp = (BRIDGE / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             *compile_files], root / "compile.log")
    legacy_cp = str(classes) + ";" + cp
    (root / "historical-classpath.txt").write_text(legacy_cp, encoding="utf-8")
    (root / "control-classpath.txt").write_text(cp, encoding="utf-8")
    return legacy_cp, cp


def legacy_run(root, cp, nominal):
    folder = root / "audit" if nominal else root / "trials/static" / LEGACY
    folder.mkdir(parents=True)
    stop, cap, checkpoints = ("NOMINAL", 5000, (100, 1000)) if nominal else ("ACTUAL", POINTS[-1], POINTS)
    inputs = root / "inputs"
    cmd = ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "research.dynamic.HistoricalNsgaRun",
           str(inputs / (STEM + ".txt")), str(inputs / "RECONSTRUCTED-setup.txt"), str(folder),
           stop, str(cap), str(SEED), *map(str, checkpoints)]
    write_once(folder / "command.json", cmd)
    print("START", LEGACY, stop, cap, flush=True)
    start = time.monotonic()
    code = None
    try:
        with (folder / "run.log").open("x", encoding="utf-8") as stream:
            code = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=600).returncode
    finally:
        write_once(folder / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - start})
    if code != 0:
        raise RuntimeError((folder / "run.log").read_text(encoding="utf-8", errors="replace")[-2500:])
    receipt, = rows(folder / "run-receipt.jsonl")
    summary = read(folder / "summary.json")
    curve = rows(folder / "anytime.jsonl")
    solutions = rows(folder / "solutions.jsonl")
    assert len(solutions) == summary["archiveSize"] == summary["offlineValidationDecodes"]
    assert receipt["stopRule"] == stop and receipt["seed"] == SEED and receipt["failed"] == 0
    assert receipt["physicalCalls"] == receipt["physicalSuccesses"] == receipt["attempted"] == receipt["successful"]
    assert [p["fe"] for p in curve] == list(checkpoints) and all(p["reached"] for p in curve)
    if nominal:
        assert receipt["stopReason"] == "ALGORITHM_RETURNED" and receipt["nominalCounter"] >= cap
        assert receipt["physicalCalls"] < cap
        verify_audit_log(folder, receipt)
    else:
        assert receipt["stopReason"] == "FE_LIMIT" and receipt["physicalCalls"] == cap
        assert objectives(curve[-1]["front"]) == objectives(row["objectives"] for row in solutions)
    print("PASS", LEGACY, stop, receipt["nominalCounter"], receipt["physicalCalls"], flush=True)
    return {"receipt": receipt, "curve": curve, "replays": len(solutions)}


def verify_audit_log(folder, receipt):
    log = (folder / "run.log").read_text(encoding="utf-8")
    generation_rows = [tuple(map(int, row)) for row in re.findall(
        r"AUDIT generation=(\d+) nominal=(\d+) physical=(\d+) reproductionIncrement=(\d+)", log)]
    old_nominal = old_physical = 100
    for step, (generation, nominal, physical, extra) in enumerate(generation_rows, 1):
        assert generation == step and nominal - old_nominal == 100 + extra and physical - old_physical == 100
        old_nominal, old_physical = nominal, physical
    assert len(generation_rows) == receipt["generationsCompleted"]
    assert (old_nominal, old_physical) == (receipt["nominalCounter"], receipt["physicalCalls"])
    write_once(folder / "counter-trajectory.json", [{"generation": g, "nominal": n, "physical": p, "reproductionIncrement": e}
                                                     for g, n, p, e in generation_rows])


def verify_controls(runs):
    for mode in ("BASELINE", "NSGA2_4V"):
        old = rows(BRIDGE / "trials/static" / mode / "anytime.jsonl")
        now = {p["fe"]: p for p in runs[mode]["curve"]}
        assert all(objectives(p["front"]) == objectives(now[p["fe"]]["front"]) for p in old)
    assert all(objectives(run["curve"][0]["front"]) == objectives(runs["BASELINE"]["curve"][0]["front"])
               for run in runs.values())


def main():
    root = ROOT / "runs" / datetime.now().strftime("historical-nsga-comparison-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("HISTORICAL_ROOT", root, flush=True)
    start = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            legacy_cp, cp = prepare_legacy(root)
            short = legacy_run(root, legacy_cp, nominal=True)
            long = legacy_run(root, legacy_cp, nominal=False)
            assert all(objectives(a["front"]) == objectives(b["front"]) for a, b in zip(short["curve"], long["curve"]))
            trials = {LEGACY: long}
            for mode in ("BASELINE", "NSGA2_4V"):
                trials[mode] = run_one(root, cp, "static", mode, POINTS)
            verify_controls(trials)
            analyze(root, {"static": trials}, read(BRIDGE / "protocol.json")["normalization"])
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(error),
                                         "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "performanceFE": 1500000,
                                     "nominalProbe": short["receipt"], "oldControlCurvesExact": True,
                                     "wallSeconds": time.monotonic() - start})
    print("HISTORICAL_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()

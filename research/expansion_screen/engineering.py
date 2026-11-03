"""Real-entry correctness and initialization checks, never quality-based parameter selection."""
import argparse
import json
from pathlib import Path
import shutil
import sys
from .execution import ROOT, PREVIOUS, POLICY, read, write

sys.path.insert(0, str(ROOT / "scripts"))
from baseline_build import execute


def _command(build, folder, inputs, mode, fe, seconds, seed):
    return ["java", "-Xms32m", "-Xmx2g", "-cp", (build/"classpath.txt").read_text(encoding="utf-8"),
            "research.dynamic.DynamicRun", str(inputs/(inputs.name+".txt")),
            str(inputs/"RECONSTRUCTED-setup.txt"), str(inputs/"fatigue-input.txt"), str(folder),
            mode, str(fe), str(seed), str(seconds), "1.0", "true", "false", "0", "true", "SCREEN", "0"]


def _run(build, folder, inputs, mode, fe, seconds="Infinity", seed=4242421):
    folder.mkdir(parents=True)
    execute(_command(build, folder, inputs, mode, fe, seconds, seed), folder/"run.log", 180)
    summary = read(folder/"summary.json")
    if summary["status"] != "passed" or summary["failed"] != summary["timeInterruptedAttempts"]:
        raise AssertionError("Failed real integration: " + str(folder))
    if seconds == "Infinity" and (summary["attempted"] != fe or summary["successful"] != fe):
        raise AssertionError("Fixed-FE integration was not exact")
    if summary["archiveSize"] != summary["offlineValidationDecodes"]:
        raise AssertionError("Incomplete archive replay")
    if seconds != "Infinity":
        rows = [json.loads(line) for line in (folder/"anytime.jsonl").read_text(encoding="utf-8").splitlines()]
        times = [r for r in rows if r["checkpointKind"] == "TIME"]
        if len(times) != 2 or any(r["elapsedSeconds"] > r["checkpoint"]+1e-9 for r in times):
            raise AssertionError("Invalid dual-budget time snapshots")
        censored = [r for r in rows if r["checkpointKind"] == "FE" and not r["reached"]]
        if any(r["front"] for r in censored):
            raise AssertionError("Fabricated censored FE front")
    return summary


def verify(build):
    build = build.resolve()
    policy = read(POLICY)
    stems = ["20_2_3_1", "200_8_5_1"]
    for stem in stems:
        inputs = build/"inputs"/stem
        inputs.mkdir(parents=True)
        for file in (PREVIOUS/"inputs"/stem).iterdir():
            if file.is_file():
                shutil.copy2(file, inputs/file.name)
        shutil.copy2(ROOT/"data/chapter4"/(stem+".txt"), inputs/(stem+".txt"))
    common = ["BASELINE", "TAIL", *policy["external_comparators"]]
    fingerprints, checks = [], []
    for mode in common:
        folder = build/"initialization"/mode
        _run(build, folder, build/"inputs"/stems[0], mode, 100)
        fingerprints.append((folder/"solutions.jsonl").read_bytes())
    if any(value != fingerprints[0] for value in fingerprints[1:]):
        raise AssertionError("Common free initial population changed across algorithms")
    for stem in stems:
        for mode in policy["variants"]:
            folder = build/"integration"/stem/mode
            summary = _run(build, folder, build/"inputs"/stem, mode, 1500)
            checks.append({"instance":stem, "mode":mode, "FE":1500,
                           "archiveSize":summary["archiveSize"], "replay":"passed"})
        print("REAL_INTEGRATION_PASS", stem, flush=True)
    for mode in policy["variants"]:
        _run(build, build/"time-integration"/mode, build/"inputs"/stems[0], mode,
             9223372036854775807, ".3")
    modules = ["RuntimeChecks", "DynamicRuntimeChecks", "AnytimeChecks", "SearchChecks", "JointChecks", "CooperationChecks", "ClassicChecks"]
    for module in modules:
        if not (build/(module+".log")).exists():
            raise AssertionError("Missing prerequisite engineering log: " + module)
    acceptance = {"status":"passed", "scope":"Step4 engineering only, no optimizer quality selection",
                  "engineeringRoot":str(build), "moduleChecks":modules,
                  "commonInitializationModes":common, "initializationFE":100,
                  "realIntegration":checks, "dualTimeIntegrationModes":policy["variants"],
                  "dualTimeIntegrationSeconds":.3,
                  "classicSettings":"0=mutationScale1; 1=.5; 2=2; all else fixed",
                  "SPEAUnits":"initial100 paid absolute means frozen; density/truncation normalized; dominance unchanged",
                  "VNS":"ordinary chapter4 CENTER every50 global children; cap30 intra only; inter additionally paid"}
    write(build/"acceptance.json", acceptance, once=True)
    write(build/"state.json", {"status":"STEP4_ACCEPTED", "next":"bounded performance calibration and screen"})
    print("STEP4_ACCEPTED", build, flush=True)
    return acceptance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    verify(parser.parse_args().build)

"""Execute steps 1-3 contract checks and bounded integration runs, not a quality benchmark."""
from datetime import datetime
import json
import subprocess
from baseline_build import WORKSPACE, execute
from dynamic_build import build_dynamic
from dynamic_inputs import materialize
from dynamic_reference import reference_cases


def fingerprint(folder):
    rows = [json.loads(line) for line in (folder / "solutions.jsonl").read_text(encoding="utf-8").splitlines()]
    return sorted(json.dumps(row, sort_keys=True) for row in rows)


def main():
    output = WORKSPACE / "runs" / datetime.now().strftime("dynamic-steps123-%Y%m%d-%H%M%S-%f")
    output.mkdir()
    status = {"status": "running", "scope": "correctness/integration, not performance evidence", "checks": []}
    status_path = output / "status.json"
    def save():
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    try:
        cp = build_dynamic(output)
        def java(name, main_class, *args):
            execute(["java", "-Xmx1g", "-cp", cp, main_class, *map(str, args)], output / (name + ".log"), timeout=600)
            status["checks"].append(name); save()
            print(name + ": " + (output / (name + ".log")).read_text(encoding="utf-8").splitlines()[-1], flush=True)
        java("runtime-regression", "research.RuntimeChecks")
        java("deadline-contract", "research.dynamic.DynamicRuntimeChecks")
        java("static-search-ch3", "org.uma.jmetal.util.research.search.SearchChecks", 3)
        java("static-search-ch4", "org.uma.jmetal.util.research.search.SearchChecks", 4)
        # Core worker's dedicated checks are discovered from its source package.
        java("dynamic-core", "org.uma.jmetal.util.research.modelchecks.DynamicCoreChecks")
        java("joint-contract", "org.uma.jmetal.util.research.joint.JointChecks")
        references = output / "reference"
        status["referenceCases"] = reference_cases(references, WORKSPACE / "data/chapter4")
        java("cross-language", "research.dynamic.DynamicCrossCheck", references, WORKSPACE / "data/chapter4")

        inputs = output / "inputs"; inputs.mkdir()
        instance_name = "20_2_3_1.txt"
        source = WORKSPACE / "data/chapter4" / instance_name
        materialize(source, inputs, 314159, "strong_fast", 271828)
        def run(name, mode="BASELINE", fe=1200, seed=202611101, seconds="Infinity", incremental=True, small=True, trace=0):
            folder = output / name; folder.mkdir()
            java(name, "research.dynamic.DynamicRun", source, inputs / "RECONSTRUCTED-setup.txt",
                 inputs / "fatigue-input.txt", folder, mode, fe, seed, seconds, "1.0",
                 str(incremental).lower(), str(small).lower(), trace)
            summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
            if summary["attempted"] > fe or summary["attempted"] != summary["successful"] + summary["failed"]:
                raise AssertionError("FE accounting")
            return folder, summary
        first, _ = run("baseline-inc")
        repeat, _ = run("baseline-repeat")
        full, _ = run("baseline-full", incremental=False)
        if fingerprint(first) != fingerprint(repeat) or fingerprint(first) != fingerprint(full):
            raise AssertionError("Seed reproducibility / full-incremental trajectory mismatch")
        status["checks"].append("same-seed-and-full-incremental-archives"); save()
        for fe in (0, 1, 7, 8, 9, 17):
            run("boundary-" + str(fe), fe=fe)
        _, limited = run("deadline-zero", mode="VALUE", fe=10000, seconds="0")
        if limited["stopReason"] != "TIME_LIMIT" or limited["successful"] != 0:
            raise AssertionError("Zero time budget started search")
        _, limited = run("deadline-mid", mode="VALUE", fe=100000, seconds="0.05")
        if limited["stopReason"] != "TIME_LIMIT":
            raise AssertionError("Deadline did not stop the run")
        for mode in ("RANDOM", "GREEDY", "TAIL", "VALUE"):
            _, summary = run("joint-" + mode.lower(), mode=mode, fe=2200, trace=4 if mode == "VALUE" else 0)
            if summary["search"].get("generations.completed", 0) < 1:
                raise AssertionError("Joint integration did not complete a whole generation")
            if mode in ("RANDOM", "GREEDY") and summary["joint"]["featurePrecomputeNanos"] != 0:
                raise AssertionError("Simple control pays for unused value feature preprocessing")
        _, default = run("default-complete", fe=15000, small=False)
        for direction in (1, 2, 3, 4):
            if default["search"].get(f"qgs.g{direction}.updates", 0) < 1:
                raise AssertionError("Default four-group QGS not executed")
        _, trained = run("default-value", mode="VALUE", fe=15000, small=False)
        if trained["joint"]["learnedActions"] == 0 or any(v["updates"] == 0 for v in trained["joint"]["perDirection"].values()):
            raise AssertionError("Default integration did not exercise all four trained value heads")
        status["status"] = "passed"; save()
    except Exception as error:
        status["status"] = "failed"; status["error"] = repr(error); save()
        print("Evidence:", output, flush=True)
        raise
    print("Evidence:", output, flush=True)


if __name__ == "__main__":
    main()

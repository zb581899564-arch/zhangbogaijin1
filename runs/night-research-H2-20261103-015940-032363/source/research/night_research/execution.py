"""One owned JVM at a time, bounded analysis, and no incomplete-owner retry."""
import subprocess
import sys
import time
import math

from research.semantic_repair.evidence import read, write_once
from .protocol import ROOT, trial_folder
from .trials import load_trial


def command(root, folder, job, spec):
    inputs = root / "inputs" / job["instance"]
    args = [str(inputs / (job["instance"] + ".txt")), str(inputs / "RECONSTRUCTED-setup.txt"),
        str(inputs / "fatigue-input.txt"), str(folder), spec["mode"], "9223372036854775807",
        str(job["seed"]), str(job["seconds"]), "1.0", "true", "false", "0", "true",
        "SCREEN", str(spec["setting"]), spec["profile"], "true", "false", "false", "false", "false"]
    args.extend(spec.get("extra_args", []))
    return ["java", "-Xms32m", "-Xmx2g", "-cp", (root / "classpath.txt").read_text(encoding="utf-8-sig").strip(),
        "research.dynamic.DynamicRun", *args]


def load_run(root, job, instance, spec):
    folder = trial_folder(root, job)
    if read(folder / "command.json") != command(root, folder, job, spec):
        raise ValueError("Owner command differs from the complete frozen Java invocation")
    process = read(folder / "process.json")
    if process.get("status") != "PROCESS_COMPLETE" or process.get("returnCode") != 0:
        raise ValueError("Unsuccessful process receipt cannot enter quality analysis")
    if not isinstance(process.get("processWallSeconds"), (int, float)) or not math.isfinite(process["processWallSeconds"]) or process["processWallSeconds"] < 0:
        raise ValueError("Missing or invalid owned process cost")
    run = load_trial(folder, instance, job["seed"], job["variant"], spec)
    if run["execution"] is not None:
        receipt = run["execution"]
        if any(receipt.get(key) != value for key, value in process.items()):
            raise ValueError("Controller receipt differs from its paid process receipt")
        value = receipt.get("controllerValidationSeconds")
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("Missing or invalid owned controller-validation cost")
    return run


def _dispatch(folder, cmd, allowance):
    started_epoch, started = time.time(), time.monotonic()
    code, state = None, "PROCESS_FAILED"
    try:
        with (folder / "run.log").open("x", encoding="utf-8") as stream:
            process = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=allowance)
        code = process.returncode
        state = "PROCESS_COMPLETE" if code == 0 else "PROCESS_FAILED"
    except subprocess.TimeoutExpired as error:
        state = "PROCESS_TIMEOUT"
        raise TimeoutError("Owned JVM exceeded remaining hard deadline; incomplete owner retained") from error
    finally:
        receipt = {"startedEpoch": started_epoch, "completedEpoch": time.time(),
            "processWallSeconds": time.monotonic() - started, "returnCode": code, "status": state}
        write_once(folder / "process.json", receipt)
    if code != 0:
        raise RuntimeError("Owned JVM failed; incomplete owner retained: " + str(folder))
    return receipt


def run_one(root, job, instance, spec, deadline):
    folder = trial_folder(root, job)
    expected = command(root, folder, job, spec)
    if folder.exists():
        required = ("summary.json", "solutions.jsonl", "anytime.jsonl", "semantic-trace.jsonl",
                    "command.json", "process.json", "execution.json")
        if not all((folder / name).is_file() for name in required):
            raise RuntimeError("Incomplete owner retained; no automatic retry: " + str(folder))
        if read(folder / "command.json") != expected:
            raise ValueError("Existing owner command differs from frozen job")
        return load_run(root, job, instance, spec), False
    deadline.require(job["seconds"] + 5)
    folder.mkdir(parents=True)
    write_once(folder / "command.json", expected)
    receipt = _dispatch(folder, expected, min(deadline.remaining(), max(60., job["seconds"] * 3 + 30)))
    started = time.monotonic()
    try:
        run = load_run(root, job, instance, spec)
    except BaseException as error:
        write_once(folder / "validation-failure.json", {"error": str(error),
            "controllerValidationSeconds": time.monotonic() - started})
        raise
    receipt.update({"controllerValidationSeconds": time.monotonic() - started,
        "scope": "JVM startup/search/whole returned-archive replay/export; controller validation separate; all inside original campaign clock"})
    write_once(folder / "execution.json", receipt)
    run["execution"] = receipt
    deadline.require()
    return run, True


def analyze_bounded(root, deadline):
    deadline.require(5)
    tag = str(time.time_ns())
    receipt = root / ("analysis-result-" + tag + ".json")
    cmd = [sys.executable, "-B", "-m", "research.night_research.worker", str(root), str(receipt)]
    write_once(root / ("analysis-command-" + tag + ".json"), cmd)
    try:
        with (root / ("analysis-process-" + tag + ".log")).open("x", encoding="utf-8") as stream:
            process = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=deadline.remaining())
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Original campaign/absolute night stop terminated owned analysis; partial artifacts retained") from error
    if process.returncode or not receipt.is_file():
        raise RuntimeError("Owned analysis failed; all artifacts retained")
    deadline.require()
    return root / read(receipt)["analysis"]

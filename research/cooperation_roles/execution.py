"""One owned JVM at a time; incomplete owners are never rerun."""
import subprocess
import sys
import time
from research.semantic_repair.evidence import read, write_once
from research.sync_job_audit.execution import Deadline, command as existing_command
from .protocol import ROOT, trial_folder
from .observations import load_run


def command(root, folder, job, spec):
    return existing_command(root, folder, job, spec) + ["true"]


def run_one(root, job, instance, spec, deadline):
    folder = trial_folder(root, job); expected = command(root, folder, job, spec)
    if folder.exists():
        required = ["summary.json", "solutions.jsonl", "anytime.jsonl", "semantic-trace.jsonl",
                    "feedback-trace.jsonl", "execution.json", "command.json"]
        if job["variant"] != "NSGA":
            required += ["composition-trace.jsonl", "cooperation-evidence.jsonl"]
        if not all((folder / name).is_file() for name in required):
            raise RuntimeError("Incomplete owner preserved; no rerun: " + str(folder))
        if read(folder / "command.json") != expected:
            raise ValueError("Existing owner command differs from frozen job")
        return load_run(root, job, instance, spec), False
    deadline.require(job["seconds"] + 5); folder.mkdir(parents=True)
    write_once(folder / "command.json", expected)
    started_epoch, started = time.time(), time.monotonic()
    try:
        with (folder / "run.log").open("x", encoding="utf-8") as stream:
            result = subprocess.run(expected, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                timeout=min(deadline.remaining(), max(60., job["seconds"] * 3 + 30)))
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Owned JVM exceeded allowance; incomplete owner retained") from error
    process_wall = time.monotonic() - started
    if result.returncode:
        raise RuntimeError("Owned JVM failed; incomplete owner retained: " + str(folder))
    start = time.monotonic(); run = load_run(root, job, instance, spec)
    receipt = {"startedEpoch": started_epoch, "completedEpoch": time.time(),
        "processWallSeconds": process_wall, "controllerValidationSeconds": time.monotonic() - start,
        "scope": "JVM startup/search/QA/export; controller numeric replay separate; all inside original campaign clock"}
    write_once(folder / "execution.json", receipt); run["execution"] = receipt
    deadline.require(); return run, True


def analyze_bounded(root, deadline):
    deadline.require(5); tag = str(time.time_ns())
    receipt = root / ("analysis-result-" + tag + ".json")
    cmd = [sys.executable, "-B", "-m", "research.cooperation_roles.worker", str(root), str(receipt)]
    write_once(root / ("analysis-command-" + tag + ".json"), cmd)
    try:
        with (root / ("analysis-process-" + tag + ".log")).open("x", encoding="utf-8") as stream:
            result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=deadline.remaining())
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Original45min cap stopped owned analysis; partial artifacts retained") from error
    if result.returncode or not receipt.exists():
        raise RuntimeError("Owned offline analysis failed; evidence retained")
    deadline.require(); return root / read(receipt)["analysis"]

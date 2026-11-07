"""Original campaign clock, exclusive controller ownership, and one-JVM dispatch."""
from contextlib import contextmanager
import os
import subprocess
import sys
import time

from .evidence import read, write_once
from .protocol import ROOT
from .trials import load_trial


class CampaignDeadline:
    def __init__(self, root):
        clock = read(root / "clock.json")
        self.started = clock["startedEpoch"]
        self.limit = clock["wallCapSeconds"]
        if self.limit != 5400:
            raise ValueError("The registered 90-minute cap must not change")
        self.offset = max(0., time.time() - self.started)
        self.monotonic = time.monotonic()

    def elapsed(self):
        return self.offset + time.monotonic() - self.monotonic

    def remaining(self):
        return max(0., self.limit - self.elapsed())

    def require(self, seconds=0):
        if self.remaining() <= seconds:
            raise TimeoutError("Original campaign clock has insufficient time; evidence preserved")


@contextmanager
def controller_lock(root, name="controller.lock"):
    """Kernel lock prevents a second resume from dispatching another JVM."""
    with (root / name).open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("Another controller owns this campaign") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def command(root, folder, job, spec):
    inputs = root / "inputs" / job["instance"]
    args = [str(inputs / (job["instance"] + ".txt")), str(inputs / "RECONSTRUCTED-setup.txt"),
            str(inputs / "fatigue-input.txt"), str(folder), spec["mode"], "9223372036854775807",
            str(job["seed"]), str(job["seconds"]), "1.0", "true", "false", "0", "true",
            "SCREEN", "0", spec["profile"], "true"]
    return ["java", "-Xms32m", "-Xmx2g", "-cp", (root / "classpath.txt").read_text(encoding="utf-8").strip(),
            "research.dynamic.DynamicRun", *args]


def run_one(root, folder, job, instance, spec, deadline):
    expected_command = command(root, folder, job, spec)
    if folder.exists():
        required = ("summary.json", "anytime.jsonl", "solutions.jsonl", "semantic-trace.jsonl", "command.json")
        if not all((folder / name).is_file() for name in required):
            raise RuntimeError("Incomplete owner preserved; will not rerun: " + str(folder))
        if read(folder / "command.json") != expected_command:
            raise ValueError("Existing owner command differs from its frozen job")
        return load_trial(folder, instance, job["seed"], job["variant"], spec), False
    deadline.require(job["seconds"] + 5)
    folder.mkdir(parents=True)
    write_once(folder / "command.json", expected_command)
    allowance = min(deadline.remaining(), max(60., job["seconds"] * 3 + 30))
    started_epoch, started_monotonic = time.time(), time.monotonic()
    try:
        with (folder / "run.log").open("x", encoding="utf-8") as stream:
            result = subprocess.run(expected_command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=allowance)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Owned JVM exceeded its allowance; partial owner preserved: " + str(folder)) from error
    deadline.require()
    if result.returncode:
        raise RuntimeError("Owned JVM failed; partial owner preserved: " + str(folder))
    process_wall = time.monotonic() - started_monotonic
    validation_start = time.monotonic()
    run = load_trial(folder, instance, job["seed"], job["variant"], spec)
    receipt = {"startedEpoch": started_epoch, "completedEpoch": time.time(),
               "processWallSeconds": process_wall,
               "controllerValidationSeconds": time.monotonic() - validation_start,
               "scope": "JVM startup/search/offline replay/export included in process wall; controller validation separate"}
    write_once(folder / "execution.json", receipt)
    run["execution"] = receipt
    return run, True


def analyze_bounded(root, deadline):
    """An owned offline worker can be terminated at the original hard cap."""
    deadline.require(10)
    tag = str(time.time_ns())
    receipt = root / ("analysis-result-" + tag + ".json")
    cmd = [sys.executable, "-m", "research.semantic_repair.analysis_worker", str(root), str(receipt)]
    write_once(root / ("analysis-command-" + tag + ".json"), cmd)
    try:
        with (root / ("analysis-process-" + tag + ".log")).open("x", encoding="utf-8") as stream:
            result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=deadline.remaining())
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Original campaign cap interrupted the owned offline analysis; partial analysis preserved") from error
    if result.returncode or not receipt.exists():
        raise RuntimeError("Offline analysis failed; owned log and partial artifacts preserved")
    deadline.require()
    return root / read(receipt)["analysis"]

"""Immutable inputs, source receipt, guarded subprocesses and the campaign deadline."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "research/dynamic_benchmark/expansion_screen_v1.json"
PREVIOUS = ROOT / "runs/dynamic-step45-20261101-192250-613958"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value, *, once=False):
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    if once:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        is_status = path.name == "status.json"
        if is_status:
            events = path.parent / "status-events"
            events.mkdir(exist_ok=True)
            event = events / (str(time.time_ns()) + ".json")
            event.write_text(payload, encoding="utf-8")
        temporary = path.with_suffix(path.suffix + ".pending")
        temporary.write_text(payload, encoding="utf-8")
        for attempt in range(20):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                if attempt < 19:
                    time.sleep(.025)
                elif not is_status:
                    raise
        # A Windows reader may deny delete/rename while permitting reads.
        # The append-only event remains the authoritative progress receipt.
        print("STATUS_PROJECTION_LOCKED", path, "see status-events", flush=True)


class CampaignDeadline:
    def __init__(self, root, started_epoch=None):
        self.root = root
        self.started = time.time() if started_epoch is None else started_epoch
        self._elapsed_offset = max(0., time.time()-self.started)
        self._monotonic_start = time.monotonic()
        self.limit = 5400

    def elapsed(self):
        return self._elapsed_offset + time.monotonic() - self._monotonic_start

    def remaining(self):
        return max(0., self.limit - self.elapsed())

    def require(self, seconds):
        if self.remaining() < seconds:
            raise TimeoutError("Campaign cap: insufficient time for the next complete unit")


def freeze_classpath(classpath, root):
    result, receipt = [], []
    binary = root / "binary"
    binary.mkdir()
    for index, item in enumerate(classpath.split(";")):
        source = Path(item)
        if not source.exists():
            raise FileNotFoundError(source)
        target = binary / ("cp-" + str(index) + (".jar" if source.is_file() else ""))
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        result.append(str(target.resolve()))
        receipt.append({"source":str(source.resolve()), "frozen":str(target.relative_to(root))})
    write(root / "classpath-sources.json", receipt, once=True)
    return ";".join(result)


def prepare(engineering):
    acceptance = read(engineering / "acceptance.json")
    if acceptance.get("status") != "passed":
        raise RuntimeError("Step4 acceptance is not passed")
    root = ROOT / "runs" / datetime.now().strftime("expansion-screen-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    deadline = CampaignDeadline(root)
    policy = read(POLICY)
    old = read(PREVIOUS / "protocol.json")
    rows = {row["stem"]:row for row in old["instances"]}
    for row in policy["instances"]:
        stem = row["stem"]
        target = root / "inputs" / stem
        target.mkdir(parents=True)
        for file in (PREVIOUS / "inputs" / stem).iterdir():
            if file.is_file():
                shutil.copy2(file, target / file.name)
        shutil.copy2(ROOT / "data/chapter4" / (stem + ".txt"), target / (stem + ".txt"))
        row["normalization"] = rows[stem]["normalization"]
        row["normalization"]["reference"] = policy["metrics"]["primary_reference"]
    cp = freeze_classpath((engineering / "classpath.txt").read_text(encoding="utf-8"), root)
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write(root / "policy.json", read(POLICY), once=True)
    write(root / "protocol.json", policy, once=True)
    write(root / "clock.json", {"startedEpoch":deadline.started, "wallCapSeconds":deadline.limit}, once=True)
    write(root / "engineering-acceptance.json", acceptance, once=True)
    write(root / "status.json", {"status":"PREPARED", "completed":0, "expected":policy["runs"]})
    snapshot_sources(root)
    return root, policy, deadline


def snapshot_sources(root):
    paths = [p for folder in [ROOT/"src/java", ROOT/"src/algorithms"] for p in folder.rglob("*.java")]
    paths += list((ROOT/"research/expansion_screen").glob("*.py"))
    paths += list((ROOT/"research/dynamic_benchmark").glob("*.py")) + [POLICY]
    manifest = {}
    for path in sorted(paths):
        relative = path.relative_to(ROOT)
        payload = path.read_bytes()
        target = root / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        manifest[str(relative)] = hashlib.sha256(payload).hexdigest()
    write(root / "source-manifest.json", manifest, once=True)


def command(root, folder, stem, variant, seed, seconds, setting=0):
    inputs = root / "inputs" / stem
    return ["java", "-Xms32m", "-Xmx2g", "-cp", (root/"classpath.txt").read_text(encoding="utf-8"),
            "research.dynamic.DynamicRun", str(inputs/(stem+".txt")), str(inputs/"RECONSTRUCTED-setup.txt"),
            str(inputs/"fatigue-input.txt"), str(folder), variant, str(9223372036854775807), str(seed),
            str(seconds), "1.0", "true", "false", "0", "true", "SCREEN", str(setting)]


def run_one(root, folder, stem, variant, seed, seconds, setting, deadline, extra_cap=None):
    if (folder / "summary.json").exists() and (folder / "anytime.jsonl").exists():
        result = read(folder / "summary.json")
        if result["status"] != "passed":
            raise RuntimeError("Existing failure preserved: " + str(folder))
        return result
    if folder.exists():
        raise RuntimeError("Incomplete owner preserved: " + str(folder))
    deadline.require(seconds + 5)
    folder.mkdir(parents=True)
    cmd = command(root, folder, stem, variant, seed, seconds, setting)
    write(folder / "command.json", cmd, once=True)
    timeout = min(deadline.remaining(), max(60, seconds*3+30))
    if extra_cap is not None:
        timeout = min(timeout, extra_cap)
    try:
        with (folder/"run.log").open("x", encoding="utf-8") as stream:
            result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Owned run exceeded its wall-clock allowance; evidence preserved: " + str(folder)) from error
    if result.returncode:
        raise RuntimeError("Run failed; partial evidence preserved: " + str(folder))
    summary = read(folder / "summary.json")
    if summary["status"] != "passed" or summary["failed"] != summary["timeInterruptedAttempts"]:
        raise RuntimeError("Genuine evaluation failure: " + str(folder))
    if summary["stopReason"] != "TIME_LIMIT":
        raise RuntimeError("Run did not use its registered time budget: " + str(folder))
    return summary

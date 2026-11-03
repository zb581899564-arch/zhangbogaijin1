"""Freeze accepted Java, Python, inputs, binaries, protocol and the original clock."""
from datetime import datetime
from pathlib import Path
import platform
import shutil
import sys
import time

from research.semantic_repair.evidence import read, write_once, digest, status, _freeze_classpath
from .protocol import ROOT, INPUT_SOURCE, CLASSIC_SOURCE, RULE_SOURCE, PLAN, make_protocol, jobs
from .instance_contract import verify_materialized_header

PYTHON_FOLDERS = ("night_research", "semantic_repair", "dynamic_benchmark", "expansion_screen")


def accepted_sources(engineering):
    acceptance, manifest = read(engineering / "acceptance.json"), read(engineering / "source-manifest.json")
    if acceptance.get("status") != "passed" or not isinstance(manifest, dict) or not manifest:
        raise ValueError("Passed engineering acceptance and source manifest are required")
    for name, expected in manifest.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError("Source changed after engineering acceptance: " + name)
    return acceptance, manifest


def freeze_sources(root):
    paths = [path for folder in ("src/java", "src/algorithms") for path in (ROOT / folder).rglob("*.java")]
    paths += [ROOT / "research/__init__.py", PLAN, RULE_SOURCE]
    paths += [path for folder in PYTHON_FOLDERS for path in (ROOT / "research" / folder).glob("*.py")]
    manifest = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT)
        target = root / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        manifest[str(relative)] = digest(target)
    write_once(root / "source-manifest.json", manifest)


def validate_new_campaign(protocol):
    """A prepared hypothesis has one owner; resume it instead of creating a replacement."""
    seeds = set(protocol["algorithm_seeds"])
    for path in (ROOT / "runs").glob("*/protocol.json"):
        previous = read(path)
        old_seeds = previous.get("algorithm_seeds", [])
        if isinstance(old_seeds, list) and seeds.intersection(s for s in old_seeds if type(s) is int):
            raise ValueError("Algorithm seeds are not new: " + str(path))
        if previous.get("version") == "night-research-v1" and previous.get("hypothesis") == protocol["hypothesis"]:
            raise ValueError("This hypothesis already has a frozen owner; resume it, never retune/restart: " + str(path.parent))


def prepare(engineering, config):
    started = time.time()
    engineering = Path(engineering).resolve()
    protocol = make_protocol(read(config) if isinstance(config, (str, Path)) else config)
    from .observations import require_contracts
    require_contracts(protocol)
    if protocol["absolute_stop_epoch"] <= started:
        raise TimeoutError("Absolute night stop has already elapsed")
    validate_new_campaign(protocol)
    acceptance, accepted = accepted_sources(engineering)
    root = ROOT / "runs" / datetime.now().strftime("night-research-" + protocol["hypothesis"] + "-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    write_once(root / "clock.json", {"startedEpoch": started, "wallCapSeconds": 3600,
        "absoluteStopEpoch": protocol["absolute_stop_epoch"]})
    write_once(root / "protocol.json", protocol)
    write_once(root / "run-order.json", jobs(protocol))
    write_once(root / "historical-input-protocol.json", read(INPUT_SOURCE / "protocol.json"))
    write_once(root / "classic-selection-provenance.json", read(CLASSIC_SOURCE))
    write_once(root / "engineering-acceptance.json", acceptance)
    write_once(root / "engineering-source-manifest.json", accepted)
    for instance in protocol["instances"]:
        source = INPUT_SOURCE / "inputs" / instance["stem"]
        verify_materialized_header(source / (instance["stem"] + ".txt"), instance["stem"])
        shutil.copytree(source, root / "inputs" / instance["stem"])
    _freeze_classpath(engineering, root)
    freeze_sources(root)
    write_once(root / "runtime.json", {"python": sys.version, "executable": sys.executable,
        "platform": platform.platform(), "engineering": str(engineering)})
    files = [p for folder in ("binary", "source", "inputs") for p in (root / folder).rglob("*") if p.is_file()]
    files += [p for p in root.glob("*") if p.is_file()]
    write_once(root / "frozen-artifacts.json", {str(p.relative_to(root)): digest(p) for p in files})
    status(root, {"status": "PREPARED", "completed": 0, "expected": protocol["runs"], "startedEpoch": started})
    return root


def verify_frozen(root):
    root = Path(root).resolve()
    for name, expected in read(root / "frozen-artifacts.json").items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError("Frozen scientific artifact changed: " + name)
    for name, expected in read(root / "source-manifest.json").items():
        if name.endswith(".py") and digest(ROOT / name) != expected:
            raise ValueError("Controller/analysis dependency changed after freeze: " + name)
    if read(root / "run-order.json") != jobs(read(root / "protocol.json")):
        raise ValueError("Saved randomized block order differs")

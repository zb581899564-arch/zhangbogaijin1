"""Freeze accepted dependencies, inputs, binaries, plan, and the original clock."""
from datetime import datetime
from pathlib import Path
import platform
import shutil
import sys
import time
import numpy as np
from research.semantic_repair.evidence import read, write_once, digest, status, _freeze_classpath
from .protocol import ROOT, PREVIOUS, PLAN, make_protocol, jobs

PYTHON_FOLDERS = ("cooperation_roles", "center_last", "sync_job_audit", "semantic_repair",
                  "dynamic_benchmark", "expansion_screen")


def accepted_sources(engineering):
    acceptance = read(engineering / "acceptance.json")
    if acceptance.get("status") != "passed":
        raise ValueError("Passed engineering acceptance required")
    manifest = read(engineering / "source-manifest.json")
    if not manifest:
        raise ValueError("Missing accepted source identity")
    for name, expected in manifest.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError("Accepted source changed: " + name)
    return acceptance, manifest


def freeze_sources(root):
    paths = [path for folder in ("src/java", "src/algorithms") for path in (ROOT / folder).rglob("*.java")]
    paths += [ROOT / "research/__init__.py", PLAN]
    paths += [path for name in PYTHON_FOLDERS for path in (ROOT / "research" / name).rglob("*.py")]
    manifest = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT); target = root / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
        manifest[str(relative)] = digest(target)
    write_once(root / "source-manifest.json", manifest)


def prepare(engineering):
    started = time.time()
    engineering = Path(engineering).resolve()
    acceptance, accepted = accepted_sources(engineering)
    root = ROOT / "runs" / datetime.now().strftime("cooperation-roles-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    write_once(root / "clock.json", {"startedEpoch": started, "wallCapSeconds": 2700})
    previous = read(PREVIOUS / "protocol.json"); protocol = make_protocol(previous)
    write_once(root / "protocol.json", protocol); write_once(root / "run-order.json", jobs(protocol))
    write_once(root / "historical-input-protocol.json", previous)
    write_once(root / "engineering-acceptance.json", acceptance)
    write_once(root / "engineering-source-manifest.json", accepted)
    regression = engineering / "common-search-regression.json"
    if regression.exists():
        shutil.copy2(regression, root / regression.name)
    for row in protocol["instances"]:
        shutil.copytree(PREVIOUS / "inputs" / row["stem"], root / "inputs" / row["stem"])
    _freeze_classpath(engineering, root); freeze_sources(root)
    write_once(root / "runtime.json", {"python": sys.version, "executable": sys.executable,
        "numpy": np.__version__, "platform": platform.platform(), "engineering": str(engineering)})
    files = [path for name in ("binary", "source", "inputs") for path in (root / name).rglob("*") if path.is_file()]
    files += [path for path in root.glob("*") if path.is_file()]
    write_once(root / "frozen-artifacts.json", {str(path.relative_to(root)): digest(path) for path in files})
    status(root, {"status": "PREPARED", "completed": 0, "expected": 150, "startedEpoch": started})
    return root


def verify_frozen(root):
    for name, expected in read(root / "frozen-artifacts.json").items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError("Frozen scientific artifact changed: " + name)
    for name, expected in read(root / "source-manifest.json").items():
        if name.endswith(".py") and digest(ROOT / name) != expected:
            raise ValueError("Python dependency changed; use archived source: " + name)
    if read(root / "run-order.json") != jobs(read(root / "protocol.json")):
        raise ValueError("Saved randomized block order differs")

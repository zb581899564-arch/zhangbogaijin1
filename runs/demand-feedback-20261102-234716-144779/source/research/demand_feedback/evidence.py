"""Freeze new accepted sources plus gate, numerical inputs and prior dependencies."""
from datetime import datetime
from pathlib import Path
import platform
import shutil
import sys
import time
import numpy as np
from research.semantic_repair.evidence import read, write_once, digest, status, _freeze_classpath
from research.cooperation_roles.evidence import accepted_sources, PYTHON_FOLDERS
from .protocol import ROOT, PREVIOUS, PLAN, make_protocol, jobs


def prior_evidence():
    status = read(PREVIOUS / "final-status.json")
    if status.get("status") != "COOPERATION_ROLES_COMPLETE" or status.get("completed") != 150:
        raise ValueError("Complete150 step2 precondition required")
    decision_path = PREVIOUS / status["analysis"] / "step3-decision.json"
    gate = read(decision_path)
    if gate.get("status") != "ELIGIBLE_FIXED_DEMAND_VALIDATION" or gate.get("gateSatisfied") is not True:
        raise ValueError("Predeclared knowledge gate did not permit step3")
    frozen = read(PREVIOUS / "frozen-artifacts.json")
    for name, expected in frozen.items():
        if (name.startswith("inputs/") or name.startswith("inputs\\") or name == "protocol.json") and digest(PREVIOUS / name) != expected:
            raise ValueError("Step2 scientific input changed: " + name)
    return status, gate, str(decision_path)


def freeze_sources(root):
    paths = [path for name in ("src/java", "src/algorithms") for path in (ROOT / name).rglob("*.java")]
    paths += [ROOT / "research/__init__.py", PLAN]
    paths += [path for name in ("demand_feedback", *PYTHON_FOLDERS) for path in (ROOT / "research" / name).rglob("*.py")]
    manifest = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT); target = root / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
        manifest[str(relative)] = digest(target)
    write_once(root / "source-manifest.json", manifest)


def prepare(engineering):
    started = time.time(); engineering = Path(engineering).resolve()
    acceptance, accepted = accepted_sources(engineering)
    previous_status, gate, gate_path = prior_evidence()
    previous = read(PREVIOUS / "protocol.json"); protocol = make_protocol(previous)
    root = ROOT / "runs" / datetime.now().strftime("demand-feedback-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    write_once(root / "clock.json", {"startedEpoch": started, "wallCapSeconds": 1800})
    for name, value in (("protocol", protocol), ("run-order", jobs(protocol)),
                        ("historical-input-protocol", previous), ("prior-campaign-status", previous_status),
                        ("prior-knowledge-gate", gate), ("engineering-acceptance", acceptance),
                        ("engineering-source-manifest", accepted)):
        write_once(root / (name + ".json"), value)
    for row in protocol["instances"]:
        shutil.copytree(PREVIOUS / "inputs" / row["stem"], root / "inputs" / row["stem"])
    for name in ("common-search-regression.json", "retained-pool-replay.json"):
        if (engineering / name).exists():
            shutil.copy2(engineering / name, root / name)
    _freeze_classpath(engineering, root); freeze_sources(root)
    write_once(root / "runtime.json", {"python": sys.version, "executable": sys.executable,
        "numpy": np.__version__, "platform": platform.platform(), "engineering": str(engineering),
        "priorGateSource": gate_path})
    paths = [path for name in ("binary", "source", "inputs") for path in (root / name).rglob("*") if path.is_file()]
    paths += [path for path in root.iterdir() if path.is_file()]
    write_once(root / "frozen-artifacts.json", {str(path.relative_to(root)): digest(path) for path in paths})
    status(root, {"status": "PREPARED", "completed": 0, "expected": 90, "startedEpoch": started})
    return root


def verify_frozen(root):
    for name, expected in read(root / "frozen-artifacts.json").items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError("Frozen demand artifact changed: " + name)
    for name, expected in read(root / "source-manifest.json").items():
        if name.endswith(".py") and digest(ROOT / name) != expected:
            raise ValueError("Frozen Python dependency changed: " + name)
    if read(root / "run-order.json") != jobs(read(root / "protocol.json")):
        raise ValueError("Frozen feedback method order differs")

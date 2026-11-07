"""Versioned validation/performance artifacts; never overwrite prior runs."""
from datetime import datetime
from pathlib import Path
import platform
import shutil
import sys
import numpy as np
from research.fatigue_reuse.experiment import save
from .protocol import PROTOCOL


PACKAGES = ("fatigue_mechanism", "fatigue_topology", "fatigue_reuse", "fatigue_incremental")
KERNEL_FILES = ("fatigue_incremental/prefix.py", "fatigue_incremental/scorer.py",
                "fatigue_reuse/chain.py", "fatigue_reuse/scorer.py", "fatigue_reuse/stage0.py",
                "fatigue_mechanism/decoder.py", "fatigue_mechanism/adjoint.py")


def create(project, phase):
    output = project / "runs" / (f"fatigue-incremental-{phase}-v4-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    save(output / "protocol.json", PROTOCOL)
    save(output / "environment.json", {"python": sys.version, "executable": sys.executable, "numpy": np.__version__,
         "platform": platform.platform(), "processor": platform.processor(), "threads": 1,
         "started_local": datetime.now().isoformat()})
    for package in PACKAGES:
        for source in (project / "research" / package).rglob("*.py"):
            target = output / "source" / package / source.relative_to(project / "research" / package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return output


def validation_gate(project, validation):
    import json
    evidence = json.loads((validation / "completion.json").read_text(encoding="utf-8"))
    if evidence["status"] != "passed" or evidence["comparisons"] != 8640:
        raise ValueError("complete numerical validation must pass first")
    for relative in KERNEL_FILES:
        current = project / "research" / relative
        checked = validation / "source" / relative
        if current.read_bytes() != checked.read_bytes():
            raise ValueError(f"kernel changed since validation: {relative}")
    for filename in PROTOCOL["instances"]:
        if (project / "data/chapter4" / filename).read_bytes() != (validation / filename).read_bytes():
            raise ValueError(f"instance changed since validation: {filename}")
    return evidence

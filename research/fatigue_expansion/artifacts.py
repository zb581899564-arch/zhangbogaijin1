"""Immutable v5 artifacts and exact source/data validation gate."""
from datetime import datetime
import json
import platform
import shutil
import sys
import numpy as np
from research.fatigue_incremental.artifacts import PACKAGES, KERNEL_FILES
from research.fatigue_reuse.experiment import save
from .protocol import PROTOCOL, instances


def create(project, phase):
    output = project / "runs" / (f"fatigue-expansion-{phase}-v5-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    config = {**PROTOCOL, "instances": instances(project)}
    save(output / "protocol.json", config)
    save(output / "environment.json", {"python": sys.version, "executable": sys.executable, "numpy": np.__version__,
         "platform": platform.platform(), "processor": platform.processor(), "threads": 1,
         "started_local": datetime.now().isoformat()})
    shutil.copyfile(project / "docs/chapter4_instance_eligibility.json", output / "eligibility.json")
    shutil.copyfile(project / "docs/动态疲劳扩展验证协议-v5.md", output / "protocol_explanation.md")
    for package in (*PACKAGES, "fatigue_expansion"):
        for source in (project / "research" / package).rglob("*.py"):
            target = output / "source" / package / source.relative_to(project / "research" / package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return output


def gate(project, validation):
    evidence = json.loads((validation / "completion.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "passed"
    assert evidence["comparisons"] == PROTOCOL["validation"]["expected_comparisons"]
    # The gate covers the implemented protocol, RNG/neighbors and harness as well as kernels.
    for source in (validation / "source").rglob("*.py"):
        current = project / "research" / source.relative_to(validation / "source")
        if source.read_bytes() != current.read_bytes():
            raise ValueError(f"validated source changed: {current}")
    for name in instances(project):
        if (validation / name).read_bytes() != (project / "data/chapter4" / name).read_bytes():
            raise ValueError(f"validated instance changed: {name}")
    if (validation / "eligibility.json").read_bytes() != (project / "docs/chapter4_instance_eligibility.json").read_bytes():
        raise ValueError("eligibility manifest changed")
    return evidence

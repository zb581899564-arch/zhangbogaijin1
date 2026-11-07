"""Freeze full source/data identity for validation and performance separately."""
from datetime import datetime
import json
import platform
import shutil
import sys
import numpy as np
from .protocol import PROTOCOL
from .cases import instances
from .records import save


PACKAGES = ("fatigue_mechanism", "fatigue_topology", "fatigue_reuse", "fatigue_incremental",
            "fatigue_expansion", "fatigue_coordination", "fatigue_exchange", "fatigue_mixture", "fatigue_scale")


def create(project, kind):
    output = project/"runs"/(f"fatigue-scale-{kind}-v10-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    save(output/"protocol.json", PROTOCOL)
    save(output/"environment.json", {"python": sys.version, "executable": sys.executable,
        "numpy": np.__version__, "platform": platform.platform(), "BLAS_threads": 1})
    for package in PACKAGES:
        source = project/"research"/package
        for file in source.rglob("*.py"):
            target = output/"source"/package/file.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
    (output/"data").mkdir()
    for name in instances(project):
        shutil.copyfile(project/"data/chapter4"/name, output/"data"/name)
    shutil.copyfile(project/"docs/chapter4_instance_eligibility.json", output/"eligibility.json")
    shutil.copyfile(project/"docs/规模泛化协议-v10.md", output/"frozen_protocol.md")
    return output


def gate(project, validation):
    result = json.loads((validation/"validation.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass"
    assert json.loads((validation/"protocol.json").read_text(encoding="utf-8")) == PROTOCOL
    for file in (validation/"source").rglob("*.py"):
        assert file.read_bytes() == (project/"research"/file.relative_to(validation/"source")).read_bytes(), str(file)
    for file in (validation/"data").glob("*.txt"):
        assert file.read_bytes() == (project/"data/chapter4"/file.name).read_bytes(), str(file)
    return result

"""Freeze the explicit design, all imported research sources and input bytes."""
from datetime import datetime
import json
import platform
import shutil
import sys
import numpy as np
from .protocol import PROTOCOL, all_instances, selected_instances
from .records import save


PACKAGES = ("fatigue_mechanism", "fatigue_topology", "fatigue_reuse", "fatigue_incremental", "fatigue_teacher")


def create(project, phase):
    output = project/"runs"/(f"fatigue-teacher-{phase}-v6-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    selected = selected_instances(project)
    assert len(selected) == 13
    save(output/"protocol.json", {**PROTOCOL, "instances": selected, "all36_seed_index_order": all_instances(project)})
    save(output/"environment.json", {"python": sys.version, "executable": sys.executable, "numpy": np.__version__,
         "platform": platform.platform(), "threads": 1, "started_local": datetime.now().isoformat()})
    for name in ("chapter4_instance_eligibility.json", "教师结构学习验证协议-v6.md"):
        shutil.copyfile(project/"docs"/name, output/name)
    for package in PACKAGES:
        base = project/"research"/package
        for source in base.rglob("*.py"):
            target = output/"source"/package/source.relative_to(base)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return output


def gate(project, validation):
    result = json.loads((validation/"completion.json").read_text(encoding="utf-8"))
    assert result["status"] == "passed" and result["cases"] == PROTOCOL["validation_cases"]
    for source in (validation/"source").rglob("*.py"):
        if source.read_bytes() != (project/"research"/source.relative_to(validation/"source")).read_bytes():
            raise ValueError(f"source changed since validation: {source}")
    for name in all_instances(project):
        if (validation/name).read_bytes() != (project/"data/chapter4"/name).read_bytes():
            raise ValueError(f"data changed since validation: {name}")
    for name in ("chapter4_instance_eligibility.json", "教师结构学习验证协议-v6.md"):
        assert (validation/name).read_bytes() == (project/"docs"/name).read_bytes()
    return result

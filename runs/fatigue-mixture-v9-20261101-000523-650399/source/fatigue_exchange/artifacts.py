"""Freeze v8 with its reused sources and historical-table provenance."""
from datetime import datetime
from pathlib import Path
import json
import platform
import shutil
import sys
import numpy as np
import scipy
from .protocol import PROTOCOL
from .records import save


def create(project):
    output = project/"runs"/("fatigue-exchange-v8-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True)
    save(output/"protocol.json", PROTOCOL)
    save(output/"environment.json", {"python": sys.version, "executable": sys.executable,
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1, "platform": platform.platform()})
    prior = project/"runs"/PROTOCOL["prior_run"]
    core = prior/"source/fatigue_mechanism"
    sources = list(core.rglob("*.py"))
    assert all(s.read_bytes() == (project/"research/fatigue_mechanism"/s.relative_to(core)).read_bytes() for s in sources)
    generator_files = ("instances.py", "space.py", "protocol.py")
    assert all((prior/"source/fatigue_coordination"/n).read_bytes() == (project/"research/fatigue_coordination"/n).read_bytes() for n in generator_files)
    assert json.loads((prior/"audit.json").read_text(encoding="utf-8"))["status"] == "pass"
    for package in ("fatigue_mechanism", "fatigue_coordination", "fatigue_reuse", "fatigue_topology", "fatigue_exchange"):
        base = project/"research"/package
        for source in base.rglob("*.py"):
            destination = output/"source"/package/source.relative_to(base)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    for name in ("audit.json", "protocol.json", "provenance_audit.json"):
        shutil.copyfile(prior/name, output/("v7-"+name))
    shutil.copyfile(project/"docs/普通跨厂交换与重绑定协议-v8.md", output/"frozen_protocol.md")
    save(output/"source_provenance.json", {"v7_run": str(prior), "shared_core_files_byte_equal": len(sources),
        "v7_generator_space_protocol_byte_equal": list(generator_files),
        "reused_tables": "copied with original physical/landscape tables per development case; no recomputation fed to online search"})
    return output

"""Freeze protocol and every imported research source before numeric outcomes."""
from datetime import datetime
import json
import platform
import shutil
import sys
import numpy as np
import scipy
from .protocol import PROTOCOL
from .records import save


def create(project):
    output = project/"runs"/("fatigue-mixture-v9-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    save(output/"protocol.json", PROTOCOL)
    save(output/"environment.json", {"python": sys.version, "executable": sys.executable,
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1, "platform": platform.platform()})
    prior = project/"runs"/PROTOCOL["prior_run"]
    assert json.loads((prior/"audit.json").read_text(encoding="utf-8"))["status"] == "pass"
    checked = []
    for package, filenames in (("fatigue_mechanism", None), ("fatigue_coordination", ("instances.py", "space.py", "protocol.py")), ("fatigue_exchange", ("operators.py",))):
        base = prior/"source"/package
        sources = list(base.rglob("*.py")) if filenames is None else [base/n for n in filenames]
        for source in sources:
            relative = source.relative_to(prior/"source")
            assert source.read_bytes() == (project/"research"/relative).read_bytes()
            checked.append(str(relative))
    for package in ("fatigue_mechanism", "fatigue_coordination", "fatigue_exchange", "fatigue_mixture"):
        base = project/"research"/package
        for source in base.rglob("*.py"):
            destination = output/"source"/package/source.relative_to(base)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    for name in ("audit.json", "protocol.json", "completion.json"):
        shutil.copyfile(prior/name, output/("v8-"+name))
    shutil.copyfile(project/"docs/普通邻域互补混合协议-v9.md", output/"frozen_protocol.md")
    save(output/"source_provenance.json", {"v8_run": str(prior), "byte_equal_sources": checked,
        "single_use_controls": "both rerun in v9 runner, not compared against v8 timing"})
    return output

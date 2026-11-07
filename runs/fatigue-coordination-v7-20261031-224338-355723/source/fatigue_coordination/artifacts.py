"""Freeze v7 and preserve direct links/copies of prior evidence summaries."""
from datetime import datetime
import platform
import shutil
import sys
import numpy as np
import scipy
from .protocol import PROTOCOL
from .records import save


PRIOR = {
    "v1": "fatigue-mechanism-v1-20261031-160753-449593",
    "v2": "fatigue-topology-v2-20261031-162700-586634",
    "v3": "fatigue-reuse-v3-20261031-172612-730865",
    "v4": "fatigue-incremental-performance-v4-20261031-175805-055200",
    "v5": "fatigue-expansion-performance-v5-20261031-184248-888305",
    "v6": "fatigue-teacher-performance-v6-20261031-201641-372374",
}


def create(project):
    output = project/"runs"/("fatigue-coordination-v7-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    save(output/"protocol.json", PROTOCOL)
    save(output/"environment.json", {"python": sys.version, "executable": sys.executable,
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "platform": platform.platform(), "started_local": datetime.now().isoformat()})
    save(output/"prior_evidence_manifest.json", PRIOR)
    for package in ("fatigue_mechanism", "fatigue_coordination"):
        base = project/"research"/package
        for source in base.rglob("*.py"):
            target = output/"source"/package/source.relative_to(base)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    for name in ("v1-v6证据与四向量可控范围.md", "协调障碍诊断协议-v7.md"):
        shutil.copyfile(project/"docs"/name, output/name)
    (output/"prior_evidence").mkdir()
    for version, directory in PRIOR.items():
        for name in ("summary.json", "audit.json"):
            shutil.copyfile(project/"runs"/directory/name, output/"prior_evidence"/(version+"-"+name))
    return output

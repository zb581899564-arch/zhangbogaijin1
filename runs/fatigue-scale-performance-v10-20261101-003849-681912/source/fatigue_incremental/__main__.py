import os
import sys
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

project = Path(__file__).resolve().parents[2]
if len(sys.argv) == 2 and sys.argv[1] == "validate":
    from .validate import run
    run(project)
elif len(sys.argv) == 3 and sys.argv[1] == "run":
    from .experiment import run
    run(project, Path(sys.argv[2]).resolve())
else:
    raise SystemExit("usage: python -m research.fatigue_incremental validate | run VALIDATION_DIRECTORY")

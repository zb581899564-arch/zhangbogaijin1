import os
import sys
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

project = Path(__file__).resolve().parents[2]
if len(sys.argv) == 2 and sys.argv[1] == "validate":
    from .validation import run
    run(project)
elif len(sys.argv) == 3 and sys.argv[1] in ("run", "analyze", "report"):
    output = Path(sys.argv[2]).resolve()
    if sys.argv[1] == "run":
        from .experiment import run
        run(project, output)
    elif sys.argv[1] == "analyze":
        from .analyze import run
        run(output)
    else:
        from .report import run
        run(output)
else:
    raise SystemExit("usage: python -m research.fatigue_teacher validate | run VALIDATION | analyze PERFORMANCE | report PERFORMANCE")

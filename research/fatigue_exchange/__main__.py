"""python -m research.fatigue_exchange from the project root."""
import os
from pathlib import Path
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
from .experiment import run
from .report import finish

finish(run(Path(__file__).resolve().parents[2]))

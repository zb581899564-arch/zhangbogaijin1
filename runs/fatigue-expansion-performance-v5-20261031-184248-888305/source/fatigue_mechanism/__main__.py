"""Usage: python -m research.fatigue_mechanism (from the project directory)."""
import os
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"  # only this diagnostic process; no system settings

from .experiment import run

run(Path(__file__).resolve().parents[2])

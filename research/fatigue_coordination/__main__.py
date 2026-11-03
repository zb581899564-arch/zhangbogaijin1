"""Run from the project root: python -m research.fatigue_coordination."""
import argparse
import os
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("--analyze", type=Path, help="audit and summarize an existing completed run")
args = parser.parse_args()
from .report import finish

if args.analyze:
    finish(args.analyze)
else:
    from .experiment import run
    finish(run(Path(__file__).resolve().parents[2]))

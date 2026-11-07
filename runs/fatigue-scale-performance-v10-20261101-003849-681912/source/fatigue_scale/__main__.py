"""python -m research.fatigue_scale validate | run VALIDATION | analyze RUN."""
import os
from pathlib import Path
import sys
for name in ("OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[name]="1"
project=Path(__file__).resolve().parents[2]
if sys.argv[1]=="validate":
    from .validation import validate
    validate(project)
elif sys.argv[1]=="run":
    from .experiment import run
    from .report import finish
    finish(project,run(project,Path(sys.argv[2])))
elif sys.argv[1]=="analyze":
    from .report import finish
    finish(project,Path(sys.argv[2]))
else:
    raise SystemExit(__doc__)

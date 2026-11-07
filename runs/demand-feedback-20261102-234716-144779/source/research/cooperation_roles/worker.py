"""Owned offline worker bounded by its parent's original campaign clock."""
from pathlib import Path
import sys
from research.semantic_repair.evidence import write_once
from research.sync_job_audit.execution import Deadline
from .analysis import analyze


def main():
    root, receipt = (Path(value).resolve() for value in sys.argv[1:])
    output = analyze(root, Deadline(root))
    write_once(receipt, {"status": "passed", "analysis": str(output.relative_to(root))})


if __name__ == "__main__":
    main()

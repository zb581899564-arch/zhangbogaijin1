"""Owned offline analysis process, terminable at the original hard deadline."""
from pathlib import Path
import sys
from research.semantic_repair.evidence import write_once
from .analysis import analyze
from .clock import Deadline


def main():
    root, receipt = (Path(value).resolve() for value in sys.argv[1:])
    deadline = Deadline(root)
    deadline.require()
    output = analyze(root, deadline)
    write_once(receipt, {"analysis": str(output.relative_to(root))})


if __name__ == "__main__":
    main()

"""Owned offline worker; the controller enforces its original remaining wall cap."""
from pathlib import Path
import sys

from .analysis import analyze
from .evidence import write_once
from .execution import CampaignDeadline


def main():
    root, receipt = (Path(value).resolve() for value in sys.argv[1:])
    output = analyze(root, CampaignDeadline(root))
    write_once(receipt, {"status": "passed", "analysis": str(output.relative_to(root))})


if __name__ == "__main__":
    main()

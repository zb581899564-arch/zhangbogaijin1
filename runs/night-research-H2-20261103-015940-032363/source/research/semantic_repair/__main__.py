"""Bounded S/O repair matrix; --checks uses synthetic data and never starts Java."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--engineering", type=Path, help="Create a new campaign from accepted engineering evidence")
    action.add_argument("--resume", type=Path, help="Resume complete owners under the original 90-minute clock")
    action.add_argument("--analyze", type=Path, help="New immutable offline analysis of an already complete 210-run matrix")
    action.add_argument("--checks", action="store_true", help="Run only synthetic math/protocol checks")
    args = parser.parse_args()
    if args.checks:
        from .checks import run_checks
        run_checks()
    elif args.engineering:
        from .campaign import run
        run(args.engineering)
    elif args.resume:
        from .campaign import resume
        resume(args.resume)
    else:
        from .analysis import analyze
        from .evidence import verify_frozen
        from .execution import controller_lock
        from .protocol import ROOT
        root = args.analyze.resolve()
        with controller_lock(ROOT / "runs", "semantic-repair-controller.lock"), controller_lock(root):
            verify_frozen(root)
            analyze(root)


if __name__ == "__main__":
    main()

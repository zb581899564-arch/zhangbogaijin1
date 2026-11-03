"""Commands: check; run ENGINEERING; resume RUN_ROOT; analyze RUN_ROOT."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True); actions.add_parser("check")
    for action in ("run", "resume", "analyze"):
        actions.add_parser(action).add_argument("path", type=Path)
    args = parser.parse_args()
    if args.action == "check":
        from .checks import run_checks
        print(json.dumps(run_checks(), ensure_ascii=False, indent=2))
    elif args.action == "analyze":
        from .evidence import verify_frozen
        from .execution import analyze_bounded
        from .clock import Deadline
        root = args.path.resolve(); verify_frozen(root)
        print(analyze_bounded(root, Deadline(root)))
    else:
        from .campaign import campaign
        campaign(engineering=args.path) if args.action == "run" else campaign(resume=args.path)


if __name__ == "__main__":
    main()

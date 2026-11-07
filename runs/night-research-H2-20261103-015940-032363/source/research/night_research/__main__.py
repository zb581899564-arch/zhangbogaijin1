"""Commands: check; prepare ENGINEERING CONFIG; run ENGINEERING CONFIG; resume ROOT; analyze ROOT."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("check")
    for action in ("prepare", "run"):
        command = actions.add_parser(action)
        command.add_argument("engineering", type=Path)
        command.add_argument("config", type=Path)
    for action in ("resume", "analyze"):
        actions.add_parser(action).add_argument("root", type=Path)
    args = parser.parse_args()
    if args.action == "check":
        from .checks import run_checks
        print(json.dumps(run_checks(), ensure_ascii=False, indent=2))
    elif args.action == "prepare":
        from .evidence import prepare
        print(prepare(args.engineering, args.config))
    elif args.action == "analyze":
        from .clock import Deadline
        from .evidence import verify_frozen
        from .execution import analyze_bounded
        root = args.root.resolve()
        deadline = Deadline(root)
        deadline.require()
        verify_frozen(root)
        print(analyze_bounded(root, deadline))
    else:
        from .campaign import campaign
        print(campaign(resume=args.root) if args.action == "resume" else campaign(args.engineering, args.config))


if __name__ == "__main__":
    main()

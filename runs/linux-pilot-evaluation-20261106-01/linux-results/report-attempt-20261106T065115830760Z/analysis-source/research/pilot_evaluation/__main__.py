"""Run focused mathematical checks on Linux: python -m research.pilot_evaluation check."""
import argparse
import json

from .checks import run_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.parse_args()
    print(json.dumps(run_checks(), indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()

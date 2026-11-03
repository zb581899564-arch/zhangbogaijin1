"""Start one bounded performance screen after step4 acceptance exists."""
import argparse
from .campaign import run, resume


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--engineering", help="Accepted step4 build directory with classpath.txt and acceptance.json")
    group.add_argument("--resume", help="Existing campaign, preserving its original clock and completed owners")
    args = parser.parse_args()
    resume(args.resume) if args.resume else run(args.engineering)


if __name__ == "__main__":
    main()

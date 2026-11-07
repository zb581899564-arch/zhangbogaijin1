"""Start one bounded performance screen after step4 acceptance exists."""
import argparse
from .campaign import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engineering", required=True, help="Accepted step4 build directory with classpath.txt and acceptance.json")
    args = parser.parse_args()
    run(args.engineering)


if __name__ == "__main__":
    main()

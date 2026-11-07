import argparse
from pathlib import Path
from .analyze import run


def main():
    parser = argparse.ArgumentParser(description="Zero-FE historical H1/H2 diagnostic")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(); run(args.output)


if __name__ == "__main__":
    main()

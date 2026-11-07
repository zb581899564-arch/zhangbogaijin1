"""I/O and process boundaries for the isolated Linux donor probe reporters."""
import argparse
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import sys
import traceback


ARMS = ("R", "G", "S", "UNION")
REFERENCES = (1.5, 1.25, 2.0)
COMPARISONS = (("UNION", "R"), ("G", "R"), ("S", "R"),
               ("UNION", "G"), ("UNION", "S"))
STATE_FIELDS = ("slot", "family", "role", "resources", "keys", "objectives",
                "JS", "FA", "MA", "WA")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def json_lines(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            require(bool(line.strip()), f"Blank JSONL record: {path}:{line_number}")
            yield json.loads(line)


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def arguments(description, *, audit=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path,
                        help="Previously accepted Linux payload root containing research/")
    if audit:
        parser.add_argument("--analysis", type=Path,
                            help="Optional generated analysis.json to verify independently")
    return parser.parse_args()


def initialize(args, kind):
    require(sys.platform.startswith("linux"), "This program only runs on Linux; no Windows statistics")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    args.root, args.library = args.root.resolve(strict=True), args.library.resolve(strict=True)
    require((args.library / "research/pilot_evaluation/__init__.py").is_file(),
            "--library must contain accepted research/pilot_evaluation")
    sys.path.insert(0, str(args.library))
    library = importlib.import_module("research.pilot_evaluation")
    require(Path(library.__file__).resolve().is_relative_to(args.library), "Wrong evaluation library imported")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = args.root / "report" / f"{kind}-{stamp}-{os.getpid()}"
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "invocation.json", dict(kind=kind, root=str(args.root),
               library=str(args.library), platform=sys.platform, argv=sys.argv,
               evaluationModule=str(Path(library.__file__).resolve())))
    return output


def record_failure(output, error):
    write_json(output / "failure.json", dict(passed=False, errorType=type(error).__name__,
               message=str(error), traceback=traceback.format_exc(), newSearchFE=0))


def protocol(root):
    plan = read_json(root / "protocol.json")
    require(set(plan["arms"]) == set(ARMS) and len(plan["arms"]) == 4, "Expected exactly four arms")
    require(plan["seeds"] == [16110003, 16110037, 16110069], "Unexpected source seed registry")
    require({item["stem"] for item in plan["instances"]} == {"20_8_5_1", "100_2_3_1"},
            "Unexpected instance registry")
    require(len(plan["instances"]) == 2, "Duplicate instances")
    return plan


def run_folder(root, stem, seed, arm):
    return root / "science" / stem / str(seed) / arm


def capture_folder(root, stem, seed):
    return root / "capture" / stem / str(seed)


def state(value):
    return {key: value[key] for key in STATE_FIELDS}

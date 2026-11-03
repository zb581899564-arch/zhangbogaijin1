"""Run one guarded, independently validated reconstructed paper baseline."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from baseline_build import WORKSPACE, build, compile_entries, execute


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=int, choices=(3, 4), required=True)
    parser.add_argument("--instance", default="20_2_3_1.txt")
    parser.add_argument("--fe", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--standby-power", type=float, required=True,
                        help="Explicit assumption: the supplied files omit this parameter")
    setup = parser.add_mutually_exclusive_group()
    setup.add_argument("--setup-file")
    setup.add_argument("--reconstruct-setup-seed", type=int)
    parser.add_argument("--diagnostic-model-exception", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if args.fe < 0:
        parser.error("FE must be nonnegative")
    if args.chapter == 4 and args.setup_file is None and args.reconstruct_setup_seed is None:
        parser.error("Chapter4 requires --setup-file or explicit --reconstruct-setup-seed")
    if args.setup_file:
        args.setup_file = str(Path(args.setup_file).resolve(strict=True))
    if not args.instance.endswith(".txt") or "/" in args.instance or "\\" in args.instance:
        parser.error("Instance must be a filename in the chapter's data directory")
    output = WORKSPACE / "runs" / datetime.now().strftime("baseline-%Y%m%d-%H%M%S-%f")
    output.mkdir()
    (output / "config.json").write_text(json.dumps(vars(args), ensure_ascii=False, indent=2), encoding="utf-8")
    classpath = compile_entries(build(args.chapter, output, args.skip_build), output, ("normalized",))
    setup_argument = ("generate:" + str(args.reconstruct_setup_seed) if args.reconstruct_setup_seed is not None
                      else str(args.setup_file or "unused"))
    command = ["java", "-Xmx1g", "-cp", classpath, "research.normalized.NormalizedRun",
               str(args.chapter), args.instance, str(args.fe), str(args.seed), str(output),
               str(WORKSPACE / "data" / f"chapter{args.chapter}"), str(args.standby_power),
               setup_argument, str(args.diagnostic_model_exception).lower()]
    try:
        execute(command, output / "run.log")
    except Exception:
        (output / "status.json").write_text(json.dumps({"status": "failed"}), encoding="utf-8")
        raise
    print((output / "run.log").read_text(encoding="utf-8").strip())
    print("Artifacts:", output)


if __name__ == "__main__":
    main()

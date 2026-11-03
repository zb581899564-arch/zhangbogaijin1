"""Run one complete dynamic four-subswarm configuration with explicit numerical inputs."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from baseline_build import WORKSPACE, execute
from dynamic_build import build_dynamic
from dynamic_inputs import materialize, PROFILES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", default="20_2_3_1.txt")
    parser.add_argument("--mode", choices=("BASELINE", "RANDOM", "GREEDY", "TAIL", "VALUE", "SYNC", "VALUE_SYNC", "SHARE", "VALUE_SHARE", "NSGA2_4V", "SPEA2_4V", "MOEAD_4V", "NSGA2_VNS_4V"), default="BASELINE")
    parser.add_argument("--fe", type=int, default=6500)
    parser.add_argument("--seconds", type=float, default=float("inf"))
    parser.add_argument("--seed", type=int, default=20261101)
    parser.add_argument("--setup-seed", type=int, default=314159)
    parser.add_argument("--parameter-seed", type=int, default=271828)
    parser.add_argument("--profile", choices=PROFILES, default="strong_fast")
    parser.add_argument("--full", action="store_true", help="Disable incremental reuse for implementation comparison")
    parser.add_argument("--small-search", action="store_true", help="Diagnostic 8-particle, Q=1 configuration")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--trace-limit", type=int, default=0, help="Paid bounded offline witness diagnostic; default disabled")
    parser.add_argument("--screen-checkpoints", action="store_true", help="Record half/full time and15000 successful FE in one run")
    parser.add_argument("--classic-setting", type=int, choices=(0, 1, 2), default=0)
    args = parser.parse_args()
    if args.fe < 0 or args.seconds < 0 or args.seconds != args.seconds or args.trace_limit < 0:
        parser.error("nonnegative budgets required")
    if Path(args.instance).name != args.instance:
        parser.error("instance must be a filename in data/chapter4")
    out = WORKSPACE / "runs" / datetime.now().strftime("dynamic-%Y%m%d-%H%M%S-%f")
    out.mkdir()
    config = vars(args).copy()
    config["seconds"] = args.seconds if args.seconds != float("inf") else None
    config["standbyPower"] = 1.0
    (out / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        instance_path = WORKSPACE / "data/chapter4" / args.instance
        _, _, metadata = materialize(instance_path, out, args.setup_seed, args.profile, args.parameter_seed)
        (out / "fatigue-source.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        cp = build_dynamic(out, args.skip_build)
        command = ["java", "-Xmx1g", "-cp", cp, "research.dynamic.DynamicRun", str(instance_path),
                   str(out / "RECONSTRUCTED-setup.txt"), str(out / "fatigue-input.txt"), str(out), args.mode,
                   str(args.fe), str(args.seed), str(args.seconds).replace("inf", "Infinity"), "1.0",
                   str(not args.full).lower(), str(args.small_search).lower(), str(args.trace_limit), "false",
                   "SCREEN" if args.screen_checkpoints else "LEGACY", str(args.classic_setting)]
        execute(command, out / "run.log", timeout=max(180, int(args.seconds + 60)) if args.seconds != float("inf") else 600)
    except Exception as error:
        (out / "status.json").write_text(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False), encoding="utf-8")
        raise
    print((out / "run.log").read_text(encoding="utf-8").strip())
    print("Artifacts:", out)


if __name__ == "__main__":
    main()

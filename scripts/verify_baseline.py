"""Run the complete necessary baseline checks without a performance experiment."""
import argparse
from datetime import datetime
import json
from baseline_build import WORKSPACE, build, compile_entries, execute


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=int, choices=(3, 4), required=True)
    parser.add_argument("--search-only", action="store_true",
                        help="Recheck search/integration after a search-only change")
    args = parser.parse_args()
    output = WORKSPACE / "runs" / datetime.now().strftime(f"baseline-checks-ch{args.chapter}-%Y%m%d-%H%M%S-%f")
    output.mkdir()
    classpath = compile_entries(build(args.chapter, output), output,
                                ("normalized", "checks", "runtimechecks", "modelchecks", "searchchecks"))
    commands = [
        ("structure", ["research.BaselineChecks", str(args.chapter), str(WORKSPACE / "data" / f"chapter{args.chapter}"), str(output / "structure-setup")]),
        ("runtime", ["research.RuntimeChecks"]),
        ("model", ["org.uma.jmetal.util.research.modelchecks.ModelChecks", str(WORKSPACE / "data/chapter3"), str(WORKSPACE / "data/chapter4")]),
        ("search", ["org.uma.jmetal.util.research.search.SearchChecks", str(args.chapter)]),
        ("integration", ["research.normalized.IntegrationChecks", str(args.chapter), str(WORKSPACE / "data" / f"chapter{args.chapter}"), str(output / "integration")]),
    ]
    if args.search_only:
        commands = commands[-2:]
    for name, arguments in commands:
        execute(["java", "-Xmx1g", "-cp", classpath, *arguments], output / f"{name}.log", timeout=180)
        lines = (output / f"{name}.log").read_text(encoding="utf-8", errors="replace").splitlines()
        print(name + ": " + lines[-1])
    (output / "status.json").write_text(json.dumps({"status":"passed","chapter":args.chapter,
                                                   "checks":[name for name, _ in commands],
                                                   "scope":"sourced reconstruction; no performance claim"}, indent=2), encoding="utf-8")
    print("Artifacts:", output)


if __name__ == "__main__":
    main()

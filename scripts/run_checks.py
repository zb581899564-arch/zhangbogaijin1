"""Build one source baseline and run bounded structural or algorithm checks."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess

WORKSPACE = Path(__file__).resolve().parents[1]
MODULES = ("jmetal-core", "jmetal-problem", "jmetal-algorithm", "jmetal-exec")


def run(command: list[str], log: Path, timeout: int = 180) -> None:
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=WORKSPACE, stdout=stream,
                                stderr=subprocess.STDOUT, text=True, timeout=timeout)
    if result.returncode:
        print(log.read_text(encoding="utf-8", errors="replace")[-4500:])
        raise RuntimeError(f"Check failed; full log: {log}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=int, choices=(3, 4), required=True)
    parser.add_argument("--mode", choices=("checks", "probe"), default="checks")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if args.mode == "probe":
        raise SystemExit("Use scripts/run_baseline.py with explicit standby and setup provenance for guarded probes")
    baseline = WORKSPACE / "baselines" / f"chapter{args.chapter}"
    logs = WORKSPACE / "runs" / datetime.now().strftime("validation-%Y%m%d-%H%M%S") / f"chapter{args.chapter}"
    logs.mkdir(parents=True, exist_ok=True)
    maven = shutil.which("mvn")
    if not maven:
        raise RuntimeError("Maven must be on PATH")
    if not args.skip_build:
        run([maven, "-o", "-f", str(baseline / "pom.xml"), "-pl", "jmetal-exec", "-am",
             "compile", "-Dmaven.test.skip=true"], logs / "build.log")
    dependency_path = baseline / "jmetal-core" / "runtime-classpath.txt"
    if not dependency_path.exists():
        run([maven, "-o", "-f", str(baseline / "jmetal-core/pom.xml"),
             "dependency:build-classpath", "-Dmdep.outputFile=runtime-classpath.txt"], logs / "classpath.log")
    classpath = ";".join([str(baseline / module / "target/classes") for module in MODULES]
                         + [dependency_path.read_text(encoding="utf-8").strip()])
    classes = logs / "classes"
    classes.mkdir(exist_ok=True)
    sources = sorted((WORKSPACE / "src/java/checks").glob("*.java"))
    run(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", classpath,
         "-d", str(classes), *map(str, sources)], logs / "compile-checks.log")
    main_class = "research.BaselineChecks" if args.mode == "checks" else "research.AlgorithmProbe"
    log = logs / f"{args.mode}.log"
    command = ["java", "-Xmx1g", "-cp", str(classes) + ";" + classpath,
               main_class, str(args.chapter), str(WORKSPACE / "data" / f"chapter{args.chapter}"),
               str(logs / "RECONSTRUCTED-check-setup")]
    run(command, log)
    print("\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-5:]))
    summary = {"chapter": args.chapter, "mode": args.mode, "status": "passed",
               "command": command, "log": str(log), "scope": "engineering validation only"}
    (logs / f"{args.mode}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Compile modular search plus its narrow checks against the selected chapter's compiled core."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=int, choices=(3, 4), required=True)
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    core = workspace / "baselines" / f"chapter{args.chapter}" / "jmetal-core" / "target/classes"
    output = workspace / "runs" / datetime.now().strftime("search-%Y%m%d-%H%M%S-%f") / f"chapter{args.chapter}"
    classes = output / "classes"
    classes.mkdir(parents=True)
    sources = []
    for directory in ("support", "model", "integration", "runtime", "search", "searchchecks"):
        sources.extend(sorted((workspace / "src/java" / directory).glob("*.java")))
    commands = [
        ["javac", "-encoding", "UTF-8", "--release", "8", "-cp", str(core), "-d", str(classes), *map(str, sources)],
        ["java", "-Xmx1g", "-cp", str(classes) + ";" + str(core),
         "org.uma.jmetal.util.research.search.SearchChecks", str(args.chapter)],
    ]
    for name, command in zip(("compile", "checks"), commands):
        result = subprocess.run(command, cwd=workspace, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=90)
        (output / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{name} failed; see {output / f'{name}.log'}\n{result.stdout}{result.stderr}")
        if result.stdout:
            print(result.stdout, end="")
    print(f"Logs: {output}")


if __name__ == "__main__":
    main()

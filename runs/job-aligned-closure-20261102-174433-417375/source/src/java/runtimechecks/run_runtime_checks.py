"""Compile and run only the shared runtime's adversarial Java 8 checks, without downloads."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=int, choices=(3, 4), required=True)
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    core = workspace / "baselines" / f"chapter{args.chapter}" / "jmetal-core" / "target" / "classes"
    if not core.exists():
        raise RuntimeError("Compile the selected baseline's core module offline first")
    output = workspace / "runs" / datetime.now().strftime("runtime-%Y%m%d-%H%M%S-%f") / f"chapter{args.chapter}"
    classes = output / "classes"
    classes.mkdir(parents=True)
    sources = sorted((workspace / "src/java/runtime").glob("*.java"))
    sources += sorted((workspace / "src/java/runtimechecks").glob("*.java"))
    commands = [
        ["javac", "-encoding", "UTF-8", "--release", "8", "-cp", str(core), "-d", str(classes), *map(str, sources)],
        ["java", "-cp", str(classes) + ";" + str(core), "research.RuntimeChecks"],
    ]
    for name, command in zip(("compile", "checks"), commands):
        result = subprocess.run(command, cwd=workspace, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=60)
        (output / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{name} failed; see {output / f'{name}.log'}\n{result.stdout}{result.stderr}")
        if result.stdout:
            print(result.stdout, end="")
    print(f"Logs: {output}")


if __name__ == "__main__":
    main()

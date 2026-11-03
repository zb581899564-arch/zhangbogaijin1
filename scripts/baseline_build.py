"""Compile a chapter source tree and small research entry points using cached dependencies."""
from pathlib import Path
import shutil
import subprocess

WORKSPACE = Path(__file__).resolve().parents[1]
MODULES = ("jmetal-core", "jmetal-problem", "jmetal-algorithm", "jmetal-exec")


def execute(command: list[str], log: Path, timeout: int = 180) -> None:
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=WORKSPACE, stdout=stream, stderr=subprocess.STDOUT,
                                text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); see {log}\n"
                           + log.read_text(encoding="utf-8", errors="replace")[-3500:])


def build(chapter: int, logs: Path, skip_maven: bool = False) -> str:
    baseline = WORKSPACE / "baselines" / f"chapter{chapter}"
    maven = shutil.which("mvn")
    if not maven:
        raise RuntimeError("Maven is not on PATH")
    if not skip_maven:
        from sync_java_modules import sync
        sync(chapter)
        execute([maven, "-o", "-f", str(baseline / "pom.xml"), "-pl", "jmetal-exec", "-am",
                 "compile", "-Dmaven.test.skip=true"], logs / "build.log")
    dependency = baseline / "jmetal-core/runtime-classpath.txt"
    if not dependency.exists():
        execute([maven, "-o", "-f", str(baseline / "jmetal-core/pom.xml"), "dependency:build-classpath",
                 "-Dmdep.outputFile=runtime-classpath.txt"], logs / "classpath.log")
    return ";".join([str(baseline / module / "target/classes") for module in MODULES]
                    + [dependency.read_text(encoding="utf-8").strip()])


def compile_entries(classpath: str, output: Path, folders: tuple[str, ...]) -> str:
    classes = output / "classes"
    classes.mkdir(exist_ok=True)
    sources = [str(path) for folder in folders for path in sorted((WORKSPACE / "src/java" / folder).glob("*.java"))]
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", classpath,
             "-d", str(classes), *sources], output / "compile-entry.log")
    return str(classes) + ";" + classpath

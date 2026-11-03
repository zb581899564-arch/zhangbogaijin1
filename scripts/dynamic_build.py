"""Build only the owned common modules and dynamic entrypoints using cached dependencies."""
from pathlib import Path
from baseline_build import WORKSPACE, build, execute


def build_dynamic(output: Path, skip_maven: bool = False) -> str:
    classpath = build(4, output, skip_maven)
    classes = output / "classes"
    classes.mkdir(exist_ok=True)
    owned = ("model", "runtime", "integration", "search", "dynamicentries", "dynamicchecks", "searchchecks", "runtimechecks", "modelchecks", "semanticchecks")
    sources = [p for folder in owned for p in sorted((WORKSPACE / "src/java" / folder).glob("*.java"))]
    sources += sorted((WORKSPACE / "src/algorithms/joint").glob("*.java"))
    sources += sorted((WORKSPACE / "src/algorithms/jointchecks").glob("*.java"))
    sources += sorted((WORKSPACE / "src/algorithms/cooperation").glob("*.java"))
    sources += sorted((WORKSPACE / "src/algorithms/cooperationchecks").glob("*.java"))
    sources += sorted((WORKSPACE / "src/algorithms/classic").glob("*.java"))
    sources += sorted((WORKSPACE / "src/algorithms/classicchecks").glob("*.java"))
    sources += sorted((WORKSPACE / "src/algorithms/mechanism").glob("*.java"))
    response = output / "javac-inputs.txt"
    response.write_text("\n".join('"' + str(p).replace("\\", "/") + '"' for p in sources), encoding="utf-8")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", classpath,
             "-d", str(classes), "@" + str(response)], output / "compile-dynamic.log")
    return str(classes) + ";" + classpath

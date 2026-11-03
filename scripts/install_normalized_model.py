"""Install the sourced model/runtime and connect the two active chapter baselines."""
from pathlib import Path
import re
import shutil
from java_source import method_body

WORKSPACE = Path(__file__).resolve().parents[1]
JAVA = Path("src/main/java/org/uma/jmetal")
PREFIX = "org.uma.jmetal.util.research."


def copy_modules(base: Path) -> None:
    target = base / "jmetal-core" / JAVA / "util/research"
    for name in ("integration", "runtime", "model", "search"):
        subdir = target if name == "integration" else target / name
        subdir.mkdir(parents=True, exist_ok=True)
        for source in (WORKSPACE / "src/java" / name).glob("*.java"):
            shutil.copy2(source, subdir / source.name)


def connect_problem(base: Path, chapter: int) -> None:
    name = "DHFSP" if chapter == 3 else "EDHHFSPW"
    path = base / "jmetal-problem" / JAVA / f"problem/multiobjective/dfsp/{name}.java"
    text = path.read_text(encoding="utf-8")
    text = text.replace(PREFIX + "InstanceFileProvider", PREFIX + "SchedulingProblemData", 1)
    text = text.replace("    private final String instanceFile;",
                        "    private final String instanceFile;\n"
                        f"    private final {PREFIX}model.Instance schedulingInstance;\n"
                        f"    @Override public {PREFIX}model.Instance getSchedulingInstance() {{ return schedulingInstance; }}")
    if chapter == 4:
        text = text.replace("return numberOfJobs_ * numberOfStages;", "return numberOfJobs_;")
    text = text.replace("        init(instanceFile);", "        init(instanceFile);\n"
                        f"        schedulingInstance = {PREFIX}SchedulingEvaluation.load(instanceFile, {chapter}, numberOfJobs, numberOfStages);")
    text = method_body(text, "public void evaluate(PermutationSolution<Integer> solution)",
                       f"        {PREFIX}SchedulingEvaluation.evaluate(solution, schedulingInstance);")
    path.write_text(text, encoding="utf-8")


def connect_initialization(base: Path, chapter: int) -> None:
    path = base / "jmetal-core" / JAVA / "solution/impl/DefaultIntegerPermutationSolution.java"
    text = path.read_text(encoding="utf-8")
    body = ("    super(problem);\n"
            f"    {PREFIX}model.Instance instance = (({PREFIX}SchedulingProblemData) problem).getSchedulingInstance();\n"
            f"    {PREFIX}SchedulingEncoding.initialize(this, instance);")
    if chapter == 4:
        body += """
    result = new int[instance.factories()][instance.stages()][];
    for (int f = 0; f < instance.factories(); f++) {
      for (int k = 0; k < instance.stages(); k++) {
        result[f][k] = new int[instance.workers(f, k)];
        for (int w = 0; w < result[f][k].length; w++) result[f][k][w] = w;
      }
    }"""
    text = method_body(text, "public DefaultIntegerPermutationSolution(PermutationProblem<?> problem)", body)
    path.write_text(text, encoding="utf-8")


def connect_search(base: Path, chapter: int) -> None:
    folder = base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/mypso"
    for name in (["MOPSODivSubDE"] if chapter == 3 else ["MOPSODivSubDE", "MOHPSOQ"]):
        path = folder / (name + ".java")
        text = path.read_text(encoding="utf-8")
        opening = text.index("{", text.index("public class " + name))
        text = text[:opening + 1] + """
    @Override public void run() {
        throw new UnsupportedOperationException("Historical search implementation is retained for audit; use CanonicalHmopso with RunContext");
    }
""" + text[opening + 1:]
        problem_name = "DHFSP" if chapter == 3 else "EDHHFSPW"
        # The Problem wrapper deliberately stays in every evaluator call. Obtain
        # immutable model data from the encoded solution's owning raw problem.
        for signature, exchange in [("insertion_fac", "true"), ("insert_otherfac", "false")]:
            marker = f"public PermutationSolution<Integer> {signature}(PermutationSolution<Integer> solution, int group)"
            body = f"""        return {PREFIX}FactoryNeighborhoods.move(solution, group, {exchange},
                (({PREFIX}SchedulingProblemData) ((org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution) solution)
                        .getSchedulingProblem()).getSchedulingInstance());"""
            text = method_body(text, marker, body)
        text = re.sub(r'int QN = 50;', "int QN = (int) Qnums;", text)
        text = re.sub(r'^\s*QN = 5;\s*$', "", text, flags=re.MULTILINE)
        path.write_text(text, encoding="utf-8")
    # No old batch launch may silently bypass the guarded runner.
    batch = base / "jmetal-exec" / JAVA / "runner/lc_psode/ALLAlgorithmRun.java"
    text = batch.read_text(encoding="utf-8")
    text = method_body(text, "public static void main(String[] args)",
                       '        throw new IllegalStateException("Use scripts/run_baseline.py: legacy batch bypasses the model/budget contract");')
    batch.write_text(text, encoding="utf-8")


def connect_random_sources(base: Path) -> None:
    folders = [base / "jmetal-core" / JAVA / "solution/impl",
               base / "jmetal-problem" / JAVA / "problem/multiobjective/dfsp",
               base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/mypso",
               base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/mymohea",
               base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/mymoead"]
    folders += [base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/nsgaii",
                base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/spea2"]
    for folder in folders:
        for path in folder.rglob("*.java"):
            text = path.read_text(encoding="utf-8")
            text = text.replace("new Random()", PREFIX + "runtime.SeededRandom.current()")
            text = text.replace("Math.random()", PREFIX + "runtime.SeededRandom.current().nextDouble()")
            text = re.sub(r'(?:java\.util\.)?Collections\.shuffle\((\w+)\)',
                          PREFIX + r'runtime.SeededRandom.shuffle(\1)', text)
            path.write_text(text, encoding="utf-8")


def main() -> None:
    for chapter in (3, 4):
        name = "DHFSP" if chapter == 3 else "EDHHFSPW"
        active = WORKSPACE / f"baselines/chapter{chapter}/jmetal-problem" / JAVA / f"problem/multiobjective/dfsp/{name}.java"
        if "SchedulingProblemData" in active.read_text(encoding="utf-8"):
            raise ValueError("Model integration already applied; use sync_java_modules.py for helper changes")
    for chapter in (3, 4):
        base = WORKSPACE / "baselines" / f"chapter{chapter}"
        copy_modules(base)
        connect_problem(base, chapter)
        connect_initialization(base, chapter)
        # Named getter avoids reflecting protected state in helper modules.
        path = base / "jmetal-core" / JAVA / "solution/impl/DefaultIntegerPermutationSolution.java"
        text = path.read_text(encoding="utf-8")
        marker = "  protected int problemflag ;"
        text = text.replace(marker, marker + "\n\n  public PermutationProblem<?> getSchedulingProblem() { return problem; }", 1)
        path.write_text(text, encoding="utf-8")
        connect_search(base, chapter)
        connect_random_sources(base)
        print("Connected sourced model and normalized runtime: chapter", chapter)


if __name__ == "__main__":
    main()

"""Apply the documented engineering repairs once to fresh baseline copies."""
from pathlib import Path
import re

WORKSPACE = Path(__file__).resolve().parents[1]
JAVA = "src/main/java/org/uma/jmetal"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one patch location in {path}: {old[:70]}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def repair_project(chapter: int) -> None:
    project = WORKSPACE / "baselines" / f"chapter{chapter}"
    pom = project / "jmetal-algorithm/pom.xml"
    text = pom.read_text(encoding="utf-8")
    text, count = re.subn(r'\s*<dependency>\s*<groupId>org.uma.jmetal</groupId>\s*<artifactId>jmetal-exec</artifactId>\s*</dependency>', "", text)
    if count != 1:
        raise ValueError("Expected original algorithm-to-exec dependency")
    pom.write_text(text, encoding="utf-8")
    pom = project / "jmetal-exec/pom.xml"
    text = pom.read_text(encoding="utf-8")
    matches = list(re.finditer(r'\s*<dependency>\s*<groupId>org.uma.jmetal</groupId>\s*<artifactId>jmetal-algorithm</artifactId>\s*</dependency>', text))
    if len(matches) != 2:
        raise ValueError("Expected duplicate algorithm dependency")
    text = text[:matches[1].start()] + text[matches[1].end():]
    pom.write_text(text, encoding="utf-8")
    core = project / "jmetal-core" / JAVA
    support = core / "util/research"
    support.mkdir(parents=True, exist_ok=True)
    for source in (WORKSPACE / "src/java/support").glob("*.java"):
        (support / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    for name in (["DHFSP"] if chapter == 3 else ["EDHHFSPW"]):
        path = project / "jmetal-problem" / JAVA / f"problem/multiobjective/dfsp/{name}.java"
        replace_once(path, f"public class {name} extends AbstractIntegerPermutationProblem{{",
                     f"public class {name} extends AbstractIntegerPermutationProblem implements "
                     "org.uma.jmetal.util.research.InstanceFileProvider {\n"
                     "    private final String instanceFile;\n\n"
                     "    @Override public String getInstanceFile() { return instanceFile; }\n"
                     "    @Override public int getWorkerVectorLength() { return "
                     + ("numberOfWorker" if chapter == 3 else "numberOfJobs_ * numberOfStages") + "; }\n")
        text = path.read_text(encoding="utf-8")
        start = text.index("        StringBuffer sbInputFileName = new StringBuffer();")
        end = text.index("        init(sbInputFileName.toString());", start) + len("        init(sbInputFileName.toString());")
        text = text[:start] + ("        instanceFile = org.uma.jmetal.util.research.SchedulingInstanceFiles.resolve(\n"
                              "                numberOfJobs, numberOfStages, numberOfFactories, problemId);\n"
                              "        init(instanceFile);") + text[end:]
        path.write_text(text, encoding="utf-8")
    solution = core / "solution/impl/DefaultIntegerPermutationSolution.java"
    text = solution.read_text(encoding="utf-8")
    text, count = re.subn(r'  static String filename = "[^"]+";', "", text)
    if count != 1:
        raise ValueError(f"Missing fixed filename in {solution}")
    marker = "    int[][] ints = readFactoryData(filename);"
    text = text.replace(marker,
                        "    String filename = org.uma.jmetal.util.research.SchedulingInstanceFiles.forProblem(problem);\n" + marker, 1)
    # The attribute map and the actual vector fields must point to the same new lists.
    marker = "    attributes = new HashMap<Object, Object>(solution.attributes) ;"
    if text.count(marker) != 1:
        raise ValueError(f"Missing copy constructor in {solution}")
    text = text.replace(marker,
                        "    for (int i = 0; i < solution.getVariablesmachine().size(); i++) {\n"
                        "      setVariableValuemachine(i, solution.getVariableValuemachine(i));\n"
                        "    }\n" + marker + "\n"
                        '    attributes.put("worker", getVariablesworker());\n'
                        '    attributes.put("machine", getVariablesmachine());', 1)
    solution.write_text(text, encoding="utf-8")
    # The inherited allocation previously hardcoded the stage count of one instance.
    generic = core / "solution/impl/AbstractGenericSolutionWithid.java"
    text = generic.read_text(encoding="utf-8")
    if chapter == 3:
        start = text.index("        //todo", text.index("variablesmachine.add(i, null)"))
        end = text.index('        attributes.put("worker",variablesworker);', start)
        text = text[:start] + ("        int workerLength = ((org.uma.jmetal.util.research.InstanceFileProvider) problem)\n"
                               "                .getWorkerVectorLength();\n"
                               "        for (int i = 0; i < workerLength; i++) {\n"
                               "            variablesworker.add(null);\n"
                               "        }\n\n") + text[end:]
    else:
        text, count = re.subn(r'private int stage\s*=\s*\d+;', "private int stage;", text)
        if count != 1:
            raise ValueError(f"Missing stage field in {generic}")
        text = text.replace("        this.problem = problem ;", "        this.problem = problem ;\n        this.stage = ((org.uma.jmetal.util.research.InstanceFileProvider) problem).getWorkerVectorLength() / problem.getNumberOfVariables();", 1)
    generic.write_text(text, encoding="utf-8")
    replace_once(generic, "        attributes.put(id, value) ;", """        if ("machine".equals(id)) {
            variablesmachine = new ArrayList<>((List<T>) value);
            value = variablesmachine;
        } else if ("worker".equals(id)) {
            variablesworker = new ArrayList<>((List<T>) value);
            value = variablesworker;
        }
        attributes.put(id, value) ;""")
    algorithm = project / "jmetal-algorithm" / JAVA / "algorithm/multiobjective/mypso/MOPSODivSubDE.java"
    text = algorithm.read_text(encoding="utf-8")
    text, count = re.subn(r'machine\.set\(numberOfMachine,\s*temp\);', "machine.set(i, temp);", text)
    if count != 1:
        raise ValueError(f"Expected machine mutation indexing defect in {algorithm}")
    algorithm.write_text(text, encoding="utf-8")
    if chapter == 3:
        replace_once(algorithm, "this.maxIterations = 300000;", "this.maxIterations = maxIterations;")
    # Obsolete sample launchers refer to APIs no longer present. The real batch
    # entry point is runner/lc_psode/ALLAlgorithmRun, which stays compiled.
    pom = project / "jmetal-exec/pom.xml"
    replace_once(pom, "        <plugins>", """        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <excludes><exclude>org/uma/jmetal/runner/myalgorithm/**</exclude></excludes>
                </configuration>
            </plugin>""")
    print(f"Applied source repairs: chapter {chapter}")


if __name__ == "__main__":
    for number in (3, 4):
        repair_project(number)

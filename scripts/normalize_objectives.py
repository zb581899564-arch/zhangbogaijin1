"""Migrate physical scheduling objectives to 0/1/2, metadata to named attributes."""
from pathlib import Path
import json
import re
import shutil

WORKSPACE = Path(__file__).resolve().parents[1]
JAVA = Path("src/main/java/org/uma/jmetal")


def migrate(chapter: int) -> dict:
    base = WORKSPACE / "baselines" / f"chapter{chapter}"
    problem_name = "DHFSP" if chapter == 3 else "EDHHFSPW"
    active_problem = base / "jmetal-problem" / JAVA / f"problem/multiobjective/dfsp/{problem_name}.java"
    if "setNumberOfObjectives(7);" not in active_problem.read_text(encoding="utf-8"):
        raise ValueError("Refusing to repeat the objective migration")
    changed = []
    algorithm = base / "jmetal-algorithm" / JAVA / "algorithm/multiobjective"
    files = [p for folder in ("mypso", "mymohea", "mymoead") for p in (algorithm / folder).glob("*.java")]
    files += [algorithm / "nsgaii/NSGAII.java", algorithm / "spea2/SPEA2.java"]
    files += list((base / "jmetal-exec" / JAVA / "runner/lc_psode").glob("*.java"))
    names = {2: "maxMakespan", 3: "minMakespan", 4: "minEnergy", 5: "maxEnergy"}
    # Active critical-factory methods are replaced separately. Preserve explicit
    # named lookups at any retained legacy call site, rather than a hidden 7D API.
    attributes = {"maxMakespan": (0, "true"), "minMakespan": (0, "false"),
                  "minEnergy": (1, "false"), "maxEnergy": (1, "true")}
    for path in files:
        old = path.read_text(encoding="utf-8")
        text = old
        for index, name in names.items():
            objective, maximum = attributes[name]
            pattern = rf'([A-Za-z_][A-Za-z_0-9]*)\.getObjective\({index}\)'
            text = re.sub(pattern,
                          rf'org.uma.jmetal.util.research.SchedulingMetadata.of(\1).extremum({objective}, {maximum})', text)
        text = text.replace("getObjective(6)", "getObjective(2)")
        if text != old:
            path.write_text(text, encoding="utf-8")
            changed.append(str(path.relative_to(base)))
    name = "DHFSP" if chapter == 3 else "EDHHFSPW"
    problem = base / "jmetal-problem" / JAVA / f"problem/multiobjective/dfsp/{name}.java"
    text = problem.read_text(encoding="utf-8")
    if "setNumberOfObjectives(7);" not in text:
        raise ValueError("Objective migration must be applied once to the engineering baseline")
    text = text.replace("setNumberOfObjectives(7);", "setNumberOfObjectives(3);")
    text = text.replace("solution.setObjective(6, f[2]);", "solution.setObjective(2, f[2]);")
    for index in (2, 3, 4, 5):
        text = re.sub(rf'^\s*solution\.setObjective\({index}, f\[[3-6]\]\);', "", text, flags=re.MULTILINE)
    # Temporary statistics for the old evaluator; the paper decoder integration
    # overwrites this entire evaluate body in the following migration.
    marker = "        solution.setObjective(2, f[2]);"
    replacement = marker + """
        double[] factoryCost = new double[numberOfFactories];
        for (int factory = 0; factory < numberOfFactories; factory++) {
            for (int stage = 0; stage < numberOfStages; stage++) {
                for (int job = 0; job < numberOfJobs_; job++) {
                    factoryCost[factory] += jobCost[factory][stage][job];
                }
            }
        }
        solution.setAttribute(org.uma.jmetal.util.research.SchedulingMetadata.KEY,
                new org.uma.jmetal.util.research.SchedulingMetadata(makespanTemp, Power, factoryCost));"""
    text = text.replace(marker, replacement, 1)
    problem.write_text(text, encoding="utf-8")
    changed.append(str(problem.relative_to(base)))
    destination = base / "jmetal-core" / JAVA / "util/research/SchedulingMetadata.java"
    shutil.copy2(WORKSPACE / "src/java/integration/SchedulingMetadata.java", destination)
    return {"chapter": chapter, "changed": changed, "objectives": ["Cmax", "TEC", "TWC"]}


if __name__ == "__main__":
    report = [migrate(chapter) for chapter in (3, 4)]
    (WORKSPACE / "docs/normalized_objective_migration.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in report:
        print(f"Chapter {item['chapter']}: migrated {len(item['changed'])} source files")

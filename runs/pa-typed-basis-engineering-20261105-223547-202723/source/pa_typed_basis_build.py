"""Build isolated typed proposal units and the frozen all-candidate timeline harness."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, execute, write_once
from pa_specialist_bridge_build import INTERFACE, replace_once
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"
SOURCE = ROOT / "runs/linkage-mixing-probe-20261105-142116-487815"


def population_source():
    text = (INTERFACE / "source/PaPopulation.java").read_text("utf-8-sig")
    changes = (
        ("    private final PaSubsetPolicy subsetPolicy;",
         '    private final PaSubsetPolicy subsetPolicy;\n    private final PaTypedTerm.Basis typedBasis = PaTypedTerm.Basis.valueOf(System.getProperty("research.pa.typedBasis","ATOM"));\n    private final PaTypedTrace typedTrace = new PaTypedTrace();'),
        ('            List<int[]> subsets = learn(); phase = "MIXING";',
         '            List<int[]> subsets = learn(); List<PaTypedTerm> terms = PaTypedTerm.expand(subsets,evaluation.catalog().jobs(),typedBasis); phase = "MIXING";'),
        ("for (int k = 0; k < subsets.size(); k++) order.add(k);", "for (int k = 0; k < terms.size(); k++) order.add(k);"),
        ("                    evaluation.checkpoint(); step = k; int donorSlot = SeededRandom.current().nextInt(population.size() - 1);\n                    if (donorSlot >= i) donorSlot++;\n                    PaIndividual parent = population.get(i), donor = population.get(donorSlot);\n                    int subsetIndex = order.get(k); PaMixingMove move = PaMixingMove.apply(evaluation.catalog(), parent.genome, donor.genome, subsets.get(subsetIndex));",
         "                    evaluation.checkpoint(); step = k; int subsetIndex = order.get(k); PaTypedTerm term = terms.get(subsetIndex);\n                    PaTypedDonors choice = PaTypedDonors.choose(evaluation.catalog(),population,i,term,SeededRandom.current());\n                    int donorSlot = choice.slot; PaIndividual parent = population.get(i), donor = donorSlot<0?parent:population.get(donorSlot);\n                    PaTypedMove move = PaTypedMove.apply(evaluation.catalog(),parent.genome,donor.genome,term,typedBasis,donorSlot<0);"),
        ("                    if (accepted) population.set(i, child);",
         "                    typedTrace.step(generation,i,k,subsetIndex,term,choice,child.paidFE);\n                    if (accepted) population.set(i, child);"),
        ("    public double[][] archive() { return archive.snapshot(); }",
         "    public double[][] archive() { return archive.snapshot(); }\n    public void finishTypedTrace() { typedTrace.close(); }"),
    )
    for old, new in changes: text = replace_once(text, old, new)
    return text


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir(); classes.mkdir()
    (source / "PaPopulation.java").write_text(population_source(), encoding="utf-8")
    genome = (INTERFACE / "source/TypedScheduleGenome.java").read_text("utf-8-sig")
    genome = replace_once(genome, "    public int[] allocations() { return allocations.clone(); }",
        '    public int allocationAt(int job) { FirstStageCatalog.range(job,allocations.length,"job"); return allocations[job]; }\n'
        '    public double priorityAt(int job) { FirstStageCatalog.range(job,priorities.length,"job"); return priorities[job]; }\n'
        "    public int[] allocations() { return allocations.clone(); }")
    (source / "TypedScheduleGenome.java").write_text(genome, encoding="utf-8")
    entry = (ENGINE / "source/PaPopulationRun.java").read_text("utf-8-sig")
    entry = replace_once(entry, "            evidence.close(); List<Map<String,Object>> front", "            population.finishTypedTrace(); evidence.close(); List<Map<String,Object>> front")
    (source / "PaPopulationRun.java").write_text(entry, encoding="utf-8")
    for path in (ROOT / "src/algorithms/diagnostics/pa_typed_basis").glob("*.java"):
        shutil.copy2(path, source / path.name)
    base = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    execute(["java", "-version"], root / "jdk-version.log")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base, "-d", str(classes),
             *map(str, source.glob("*.java"))], root / "compile.log")
    cp = str(classes) + ";" + base
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "source-hashes.json", {p.name: digest(p) for p in source.iterdir()})
    write_once(root / "class-hashes.json", class_hashes(classes))
    return cp

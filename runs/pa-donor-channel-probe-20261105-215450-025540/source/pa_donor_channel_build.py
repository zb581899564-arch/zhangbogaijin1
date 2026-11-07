"""Compile isolated channel/counter hooks; never mutate the default population/evaluator."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, execute, write_once
from pa_specialist_bridge_build import INTERFACE, replace_once
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

PROPERTY = "research.pa.donorMode"


def population_source():
    text = (INTERFACE / "source/PaPopulation.java").read_text("utf-8-sig")
    changes = (
        ("    private final PaSubsetPolicy subsetPolicy;", "    private final PaSubsetPolicy subsetPolicy;\n    private final PaDonorRollback channels;"),
        ("evaluation = evaluator; observer = evidence; subsetPolicy = java.util.Objects.requireNonNull(policy);",
         "evaluation = evaluator; observer = evidence; subsetPolicy = java.util.Objects.requireNonNull(policy); channels = new PaDonorRollback(evaluation);"),
        ("population.add(point); observer.initial(population.size() - 1, point, archive.offer(point.objectives()));",
         "population.add(point); PaInternalArchive.Flags flags = archive.offer(point.objectives());\n        observer.initial(population.size() - 1, point, flags); channels.initial(point,flags);"),
        ("population.set(i, after); observer.reencoded(generation, i, before, after);",
         "population.set(i, after); observer.reencoded(generation, i, before, after); channels.reencoded(generation,i,before,after);"),
        ("PaIndividual parent = population.get(i), donor = population.get(donorSlot);",
         "PaIndividual parent = population.get(i), donor = channels.donor(i,donorSlot,parent,population.get(donorSlot));"),
        ("                    if (accepted) population.set(i, child);",
         "                    channels.evaluated(generation,i,k,subsetIndex,subsets.get(subsetIndex),parent,donor,child,move.fallback,flags,accepted);\n                    if (accepted) population.set(i, child);"),
        ("    public double[][] archive() { return archive.snapshot(); }",
         "    public double[][] archive() { return archive.snapshot(); }\n    public java.util.Map<String,Object> channelDiagnostics() { return channels.finish(); }"),
    )
    for old, new in changes:
        text = replace_once(text, old, new)
    return text


def evaluator_source():
    text = (INTERFACE / "source/PaPaidEvaluation.java").read_text("utf-8-sig")
    text = replace_once(text, "    public PaIndividual reencode(PaIndividual before) {",
        "    long channelSeed() { return context.seed(); }\n\n    public PaIndividual reencode(PaIndividual before) {\n"
        "        return reencode(before, SeededRandom.current());\n    }\n\n    PaIndividual reencode(PaIndividual before, java.util.Random random) {")
    return replace_once(text, "FactoryKeyReencoder.apply(catalog, before.genome, SeededRandom.current())",
                         "FactoryKeyReencoder.apply(catalog, before.genome, random)")


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir(); classes.mkdir()
    for name, text in (("PaPopulation.java", population_source()), ("PaPaidEvaluation.java", evaluator_source())):
        (source / name).write_text(text, encoding="utf-8")
    text = (INTERFACE / "source/PaCapabilitySearch.java").read_text("utf-8-sig")
    text = replace_once(text, '        if(population!=null)result.put("completeGenerations",population.completedGenerations); return result;',
        '        if(population!=null) { result.put("completeGenerations",population.completedGenerations); result.putAll(population.channelDiagnostics()); } return result;')
    (source / "PaCapabilitySearch.java").write_text(text, encoding="utf-8")
    for path in (ROOT / "src/algorithms/diagnostics/pa_donor_channel").glob("*.java"):
        shutil.copy2(path, source / path.name)
    base = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    execute(["java", "-version"], root / "jdk-version.log")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base, "-d", str(classes),
             *map(str, source.glob("*.java"))], root / "compile.log")
    cp = str(classes) + ";" + base
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "class-hashes.json", class_hashes(classes))
    write_once(root / "java-source-hashes.json", {p.name: digest(p) for p in source.glob("*.java")})
    return cp

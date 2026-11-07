"""Isolate past-paid donor imports and existing uniform-preference source dispatch."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, execute
from pa_specialist_bridge_build import INTERFACE, replace_once
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest


def build(root):
    source,classes=root/"source",root/"classes";source.mkdir();classes.mkdir()
    pop=(INTERFACE/"source/PaPopulation.java").read_text("utf-8-sig")
    changes=(
        ("    private final PaSubsetPolicy subsetPolicy;","    private final PaSubsetPolicy subsetPolicy;\n    private PaBorrowedPool borrowed;"),
        ('        if (population.size() != 100) throw new IllegalStateException("Expected100initial points");',
         '        if (population.size() != 100) throw new IllegalStateException("Expected100initial points");\n        borrowed = new PaBorrowedPool(evaluation,population.get(0));'),
        ('            List<int[]> subsets = learn(); phase = "MIXING";',
         '            borrowed.refresh(generation); List<int[]> subsets = learn(); phase = "MIXING";'),
        ("                    evaluation.checkpoint(); step = k; int donorSlot = SeededRandom.current().nextInt(population.size() - 1);\n                    if (donorSlot >= i) donorSlot++;\n                    PaIndividual parent = population.get(i), donor = population.get(donorSlot);",
         "                    evaluation.checkpoint(); step = k; PaBorrowedPool.Choice choice = borrowed.choose(population,i);\n                    int donorSlot = choice.slot; PaIndividual parent = population.get(i), donor = choice.point;"),
        ("    public double[][] archive() { return archive.snapshot(); }",
         "    public double[][] archive() { return archive.snapshot(); }\n    public java.util.Map<String,Object> borrowedDiagnostics() { return borrowed==null?java.util.Collections.emptyMap():borrowed.finish(); }")
    )
    for old,new in changes:pop=replace_once(pop,old,new)
    (source/"PaPopulation.java").write_text(pop,encoding="utf-8")
    evaluator=(INTERFACE/"source/PaPaidEvaluation.java").read_text("utf-8-sig")
    methods='''    public PaIndividual borrowed(FourVectors vectors,double[] objectives,long paid,long id,PaIndividual template) {
        PermutationSolution<Integer> point=copy(template.point);write(point,vectors);
        point.getAttributes().remove(org.uma.jmetal.util.research.DynamicEvaluation.KEY);
        point.getAttributes().remove("cooperation.family");point.getAttributes().remove("cooperation.fixedFactoryByJob");
        for(int k=0;k<3;k++)point.setObjective(k,objectives[k]);
        return new PaIndividual(id,paid,Direction.CENTER,TypedScheduleGenome.fromVectors(catalog,vectors),point);
    }
    public PaIndividual borrowedView(TypedScheduleGenome genes,PaIndividual source) {
        PermutationSolution<Integer> point=copy(source.point);write(point,genes.toVectors());
        return new PaIndividual(source.id,source.paidFE,source.role,genes,point);
    }

'''
    evaluator=replace_once(evaluator,"    private void evaluate(PermutationSolution<Integer> point) {",methods+"    private void evaluate(PermutationSolution<Integer> point) {")
    (source/"PaPaidEvaluation.java").write_text(evaluator,encoding="utf-8")
    search=(INTERFACE/"source/PaCapabilitySearch.java").read_text("utf-8-sig")
    search=replace_once(search,"        SearchConfig cfg = new SearchConfig();",
        '        if(arm.equals("FULL_SHARED_DEEP") && Boolean.getBoolean("research.pa.sourceUniform")) mode += "_UNIFORM";\n        SearchConfig cfg = new SearchConfig();')
    search=replace_once(search,'        if(population!=null)result.put("completeGenerations",population.completedGenerations); return result;',
        '        if(population!=null) { result.put("completeGenerations",population.completedGenerations); result.putAll(population.borrowedDiagnostics()); } return result;')
    (source/"PaCapabilitySearch.java").write_text(search,encoding="utf-8")
    for path in (ROOT/"src/algorithms/diagnostics/pa_paid_donors").glob("*.java"):shutil.copy2(path,source/path.name)
    # The all-paid-timeline engineering entry uses the same implementation.
    engine=ROOT/"runs/pa-population-engineering-20261105-164116-698339"
    entry=(engine/"source/PaPopulationRun.java").read_text("utf-8-sig")
    entry=replace_once(entry,"        PaPopulation population = new PaPopulation(evaluation, evidence); boolean complete = false;",
        "        PaBorrowedPool.validation(instance,params); PaPopulation population = new PaPopulation(evaluation,evidence); boolean complete=false;")
    entry=replace_once(entry,"            evidence.close(); List<Map<String,Object>> front", "            java.util.Map<String,Object> borrowCounts=population.borrowedDiagnostics(); evidence.close(); List<Map<String,Object>> front")
    entry=replace_once(entry,'"expectedFE", limit,','"borrow",borrowCounts,"expectedFE", limit,')
    (source/"PaPopulationRun.java").write_text(entry,encoding="utf-8")
    base=(INTERFACE/"classpath.txt").read_text("utf-8-sig").strip()
    execute(["java","-version"],root/"jdk-version.log")
    execute(["javac","-encoding","UTF-8","--release","8","-cp",base,"-d",str(classes),*map(str,source.glob("*.java"))],root/"compile.log")
    cp=str(classes)+";"+base;(root/"classpath.txt").write_text(cp,encoding="utf-8")
    write_once(root/"source-hashes.json",{p.name:digest(p) for p in source.glob("*.java")});write_once(root/"class-hashes.json",class_hashes(classes))
    return cp

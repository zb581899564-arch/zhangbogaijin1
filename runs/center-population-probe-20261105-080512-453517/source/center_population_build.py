"""Patch only a frozen isolated CanonicalHmopso and entry; reuse accepted search dependencies."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, execute, write_once
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes

ENTRY=ROOT/'runs/natural-local-audit-20261105-073204-330248'
CANON=ROOT/'runs/group-survival-gate-20261104-234602-311536'


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    body=(CANON/'source/CanonicalHmopso.java').read_text('utf-8')
    body=replace(body,'    private boolean started;','    private boolean started;\n    private final CenterPopulationEvolution centerPopulation;')
    body=replace(body,'        guarded = (BudgetedProblem<PermutationSolution<Integer>>) problem;',
        '        guarded = (BudgetedProblem<PermutationSolution<Integer>>) problem;\n'
        '        centerPopulation=CenterPopulationEvolution.enabled()?new CenterPopulationEvolution(instance,state,support,audit,mechanism):null;')
    body=replace(body,'    private List<Particle> qgs(List<Particle> group, Direction direction) {',
        '    private List<Particle> qgs(List<Particle> group, Direction direction) {\n'
        '        if(direction==Direction.CENTER && centerPopulation!=null) return centerPopulation.evolve(group,config.qIterations);')
    (source/'CanonicalHmopso.java').write_text(body,encoding='utf-8')
    entry=(ENTRY/'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun','CenterPopulationRun')
    entry=replace(entry,'        NaturalRunEvidence.identity(out);',
        '        NaturalRunEvidence.identity(out);\n'
        '        lines(out.resolve("center-class-identity.json"),Collections.singletonList(ClassResolutionProbe.capture('\
        '"org.uma.jmetal.util.research.search.CenterPopulationEvolution","org.uma.jmetal.util.research.classic.CenterMatingScores",'\
        '"org.uma.jmetal.util.research.classic.NsgaSelection","org.uma.jmetal.util.research.classic.ClassicVariation")));')
    entry=replace(entry,'        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n'
        '        lines(out.resolve("center-population.json"),Collections.singletonList(org.uma.jmetal.util.research.search.CenterPopulationEvolution.diagnostics()));')
    (source/'CenterPopulationRun.java').write_text(entry,encoding='utf-8')
    for name in ('CenterPopulationEvolution','CenterMatingScores','CenterPopulationChecks'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    shutil.copy2(ROOT/'src/algorithms/classic/ClassicKernelBridge.java',source)
    for name in ('center_population_build.py','run_center_population_probe.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(ENTRY/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'class-hashes.json',class_hashes(classes));return cp

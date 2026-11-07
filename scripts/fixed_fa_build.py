"""Isolated mask on verified frozen variation sources; accepted entry plus common initialization/guard adapter."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT,execute,write_once
from paired_survival_bench import class_hashes
from run_paired_qgs_guidance import replace

ENTRY=ROOT/'runs/natural-local-audit-20261105-073204-330248'
SOURCE=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
FROZEN=ROOT/'runs/night-research-H1-20261103-010138-848045'
IDENTITY=ROOT/'runs/fixedfa-source-contract-20261105-085918-475048'


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    aligned=(IDENTITY/'source/JobAlignedResources.java').read_text('utf-8')
    aligned=replace(aligned,'        if (r4 < config.factoryMutation) mutateFactory(child, instance, random);',
        '        if (r4 < config.factoryMutation && !org.uma.jmetal.util.research.search.FixedFAMutationMask.skipAligned()) mutateFactory(child, instance, random);')
    (source/'JobAlignedResources.java').write_text(aligned,encoding='utf-8')
    classic=(IDENTITY/'source/ClassicVariation.java').read_text('utf-8')
    classic=replace(classic,'            if (random.nextDouble() < mutation) genes[j][0] = alternative(genes[j][0], instance.factories(), random);',
        '            if (random.nextDouble() < mutation && !org.uma.jmetal.util.research.search.FixedFAMutationMask.skipClassic()) genes[j][0] = alternative(genes[j][0], instance.factories(), random);')
    (source/'ClassicVariation.java').write_text(classic,encoding='utf-8')
    body=(ENTRY/'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun','FixedFARun')
    body=replace(body,'        RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,limit,seed,seconds);',
        '        FixedFactoryProblem fixedProblem=new FixedFactoryProblem(decoder,in);\n'
        '        RunContext<PermutationSolution<Integer>> context=new RunContext<>(fixedProblem,limit,seed,seconds);')
    body=replace(body,'        NaturalRunEvidence.identity(out);',
        '        NaturalRunEvidence.identity(out);\n'
        '        lines(out.resolve("fixedfa-class-identity.json"),Collections.singletonList(ClassResolutionProbe.capture('\
        '"research.dynamic.FixedFactoryProblem","org.uma.jmetal.util.research.search.FixedFAMutationMask",'\
        '"org.uma.jmetal.util.research.mechanism.JobAlignedResources","org.uma.jmetal.util.research.classic.ClassicVariation")));')
    body=replace(body,'        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n'
        '        lines(out.resolve("fixedfa-constraint.json"),Collections.singletonList(fixedProblem.diagnostics()));')
    (source/'FixedFARun.java').write_text(body,encoding='utf-8')
    for name in ('FixedFAMutationMask','FixedFactoryProblem','FixedFAGuardChecks','FactoryAssignmentEncoding','FactoryAssignmentChecks'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('fixed_fa_build.py','fixed_fa_inputs.py','fixed_fa_execution.py','fixed_fa_analysis.py','run_fixed_fa_conditional.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(ENTRY/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8');return cp

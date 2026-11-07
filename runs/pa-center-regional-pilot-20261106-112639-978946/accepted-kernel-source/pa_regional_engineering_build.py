"""Build accepted math before a minimal isolated population policy adapter."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,write_once,execute
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class
from ctx_gom_build import once
from pa_regional_math import run as math_precondition


def build(root,plan):
    opportunity=Path(plan['opportunityRoot'])
    assert read(opportunity/'independent-final-audit.json')['passed'] and digest(opportunity/'independent-final-audit.json')==plan['opportunityAuditSHA256']
    source,math_classes,classes=[root/name for name in ('source','math-classes','classes')]
    for p in (source,math_classes,classes):p.mkdir()
    for p in (ROOT/'src/algorithms/diagnostics/pa_regional').glob('*.java'):shutil.copy2(p,source)
    for name in ('pa_regional_math.py','pa_regional_engineering_build.py','pa_regional_engineering_support.py','pa_regional_replay.py','run_pa_center_regional_engineering.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(Path(plan['sourceBase'])/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(math_classes),
        *[str(source/name) for name in ('CenterAssignment.java','CenterTargets.java','PaRegionalMathRun.java')]],root/'math-compile.log')
    math_cp=str(math_classes)+';'+base;math_precondition(root,math_cp,plan)
    original=Path(plan['populationSource']);text=original.read_text('utf-8')
    text=once(text,'    private final PaInternalArchive archive = new PaInternalArchive();',
        '    private final PaInternalArchive archive = new PaInternalArchive();\n    private final PaRegionalPolicy regional = PaRegionalPolicy.configured();')
    anchor='        population.add(point); observer.initial(population.size() - 1, point, archive.offer(point.objectives()));'
    text=once(text,anchor,anchor+'\n        regional.initial(population.size() - 1, point);')
    anchor='                    PaIndividual child = evaluation.candidate(move.genome, parent);'
    text=once(text,anchor,anchor+'\n                    regional.paid(child);')
    text=once(text,'boolean accepted = accepts(parent, child, flags);',
        'boolean accepted = regional.accepts(slot, parent, child, flags, accepts(parent, child, flags));')
    (source/'PaPopulation.java').write_text(text,encoding='utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',math_cp,'-d',str(classes),
        *[str(source/name) for name in ('PaRegionalPolicy.java','PaPopulation.java','PaRegionalEngineeringRun.java')]],root/'compile.log')
    cp=str(classes)+';'+math_cp;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'class-hashes.json',dict(math=class_hashes(math_classes),policy=class_hashes(classes)))
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'population-adapter.json',dict(source=str(original),sourceSHA256=digest(original),
        changes=['Add isolated policy field','Observe paid initial after native archive/evidence','Observe paid candidate before archive','Wrap original accepts output'],
        originalAcceptFunctionUnchanged=True,modelDonorFOSPopulationOrderUnchanged=True))
    inherited={}
    for suffix in ('PaPaidEvaluation','PaIndividual','PaInternalArchive','FactoryKeyReencoder','PaMixingMove','PaDependencyModel','LinkageHierarchy'):
        name='org.uma.jmetal.util.research.modelglobal.'+suffix;value=resolve_class(cp,name);assert value==resolve_class(base,name);inherited[name]=value
    write_once(root/'inherited-identities.json',inherited);return cp

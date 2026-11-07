"""Observation-only hooks on the actually loaded frozen search classes and paid evidence entry."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT,write_once,execute
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes

ENTRY=ROOT/'runs/natural-local-audit-20261105-073204-330248'
STATE=ROOT/'runs/batch-survival-study-20261104-222516-378030'
CLASSIC=ROOT/'runs/dynamic-deep-local-20261103-184901-271850'
LOCAL=ROOT/'runs/pddr-equivalence-20261104-081553-961399'


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    state=(STATE/'source/SearchState.java').read_text('utf-8')
    state=replace(state,'        if (support != null) support.beforeEvaluation(candidate, stage, direction);',
        '        FactoryAssignmentAudit.begin(candidate,stage,direction);\n        if (support != null) support.beforeEvaluation(candidate, stage, direction);')
    state=replace(state,'        problem.evaluate(candidate);','        FactoryAssignmentAudit.ready(candidate);\n        problem.evaluate(candidate);')
    (source/'SearchState.java').write_text(state,encoding='utf-8')
    classic=(CLASSIC/'source/ClassicAlgorithm.java').read_text('utf-8')
    classic=replace(classic,'        checkpoint.run(); count(stage + ".proposals");',
        '        checkpoint.run(); count(stage + ".proposals");\n        org.uma.jmetal.util.research.search.FactoryAssignmentAudit.begin(child,stage,null);')
    classic=replace(classic,'        problem.evaluate(child); count(stage + ".evaluations");',
        '        org.uma.jmetal.util.research.search.FactoryAssignmentAudit.ready(child);\n        problem.evaluate(child); count(stage + ".evaluations");')
    (source/'ClassicAlgorithm.java').write_text(classic,encoding='utf-8')
    local=(LOCAL/'source/LocalSearch.java').read_text('utf-8')
    local=replace(local,'                state.count("inter.accepted");','                state.count("inter.accepted");\n                FactoryAssignmentAudit.acceptedInter(child);')
    (source/'LocalSearch.java').write_text(local,encoding='utf-8')
    entry=(ENTRY/'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun','FactoryAssignmentRun')
    entry=replace(entry,'            lastPaid.observed(archive,fe);','            lastPaid.observed(archive,fe);\n            FactoryAssignmentAudit.paid(value,fe,changed);')
    entry=replace(entry,'        NaturalRunEvidence.identity(out);',
        '        NaturalRunEvidence.identity(out);\n        lines(out.resolve("fa-class-identity.json"),Collections.singletonList(ClassResolutionProbe.capture('\
        '"org.uma.jmetal.util.research.search.FactoryAssignmentAudit","org.uma.jmetal.util.research.search.FactoryAssignmentEncoding")));')
    entry=replace(entry,'        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n        FactoryAssignmentAudit.write(out,failure==null);')
    (source/'FactoryAssignmentRun.java').write_text(entry,encoding='utf-8')
    for name in ('FactoryAssignmentAudit','FactoryAssignmentEncoding','FactoryAssignmentChecks'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('factory_assignment_audit_build.py','factory_assignment_audit_analysis.py','run_factory_assignment_audit.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(ENTRY/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8');return cp

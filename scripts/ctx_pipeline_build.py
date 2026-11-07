"""Pure observer hooks in copies of exact capability sources, no default or search rule edits."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,execute,write_once
from research.semantic_repair.evidence import digest
from ctx_gom_build import once
from paired_survival_bench import class_hashes

SOURCE=ROOT/'runs/ctx-gom-capability-20261106-051509-678987'


def build(root):
    source=root/'source';classes=root/'classes';source.mkdir();classes.mkdir()
    originals={name:SOURCE/'source'/(name+'.java') for name in ('GomRunScope','GomWorkspace','GomLocalProgram')}
    originals['CanonicalHmopso']=SOURCE/'overrides/CanonicalHmopso.java'
    scope=originals['GomRunScope'].read_text('utf-8-sig')
    scope=once(scope,'        run = context; evidence = sink; clockProbe = synthetic; current = this;',
        '        run = context; evidence = sink; clockProbe = synthetic; current = this;\n        GomPipelineProbe.attach(this);')
    scope=once(scope,'        lastFlags = archive.offer(point.getObjectives()); lastPaid = point;',
        '        lastFlags = archive.offer(point.getObjectives()); lastPaid = point;\n        GomPipelineProbe.admission(point,fe);')
    workspace=originals['GomWorkspace'].read_text('utf-8-sig')
    workspace=once(workspace,'        scope.stage = "LOCAL";', '        scope.stage = "LOCAL";\n        GomPipelineProbe.workspace(this);')
    local=originals['GomLocalProgram'].read_text('utf-8-sig')
    local=once(local,'        w.programs++; scope.completedPrograms++;',
        '        GomPipelineProbe.program(w,preference);\n        w.programs++; scope.completedPrograms++;')
    canonical=originals['CanonicalHmopso'].read_text('utf-8-sig')
    for old,new in [
        ('        if (audit != null) audit.feedbackInitialized();','        if (audit != null) audit.feedbackInitialized();\n        GomPipelineProbe.population("INITIAL",population,state);'),
        ('            renewContexts(population);','            renewContexts(population);\n            GomPipelineProbe.population("PRE_GLOBAL",population,state);'),
        ('            List<Particle> globallyUpdated = flatten(updated);','            List<Particle> globallyUpdated = flatten(updated);\n            GomPipelineProbe.population("POST_GLOBAL",globallyUpdated,state);'),
        ('            if (chapter == 3) offspring.addAll(population);','            GomPipelineProbe.population("POST_LOCAL",offspring,state);\n            if (chapter == 3) offspring.addAll(population);'),
        ('                population = selected.survivors();','                GomPipelineProbe.selection(candidates,selected);\n                population = selected.survivors();'),
        ('            if (audit != null) audit.feedbackEnd();','            GomPipelineProbe.population("SURVIVORS",population,state);\n            if (audit != null) audit.feedbackEnd();')]:canonical=once(canonical,old,new)
    for name,text in [('GomRunScope',scope),('GomWorkspace',workspace),('GomLocalProgram',local),('CanonicalHmopso',canonical)]:
        (source/(name+'.java')).write_text(text,encoding='utf-8')
    for path in (ROOT/'src/algorithms/diagnostics/gom_pipeline').glob('*.java'):shutil.copy2(path,source)
    for name in ('ctx_pipeline_build.py','run_ctx_pipeline_probe.py'):shutil.copy2(Path(__file__).with_name(name),source)
    base=(SOURCE/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    cp=str(classes)+';'+base;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json',class_hashes(classes))
    write_once(root/'original-source-identities.json',{name:dict(path=str(p),sha256=digest(p)) for name,p in originals.items()})
    return base,cp

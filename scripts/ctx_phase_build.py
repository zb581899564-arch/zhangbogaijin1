"""Separate observer and preference overrides atop the exact accepted pipeline classpath."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,write_once,execute
from research.semantic_repair.evidence import digest
from ctx_gom_build import once
from paired_survival_bench import class_hashes

PROBE=ROOT/'runs/ctx-pipeline-probe-20261106-060047-432151'
CONTRACT=ROOT/'research/gomea_reference_audit/CTX_PHASE_ROLE_CAUSAL_V1.json'


def build(root):
    assert read(PROBE/'acceptance.json')['passed']
    assert class_hashes(PROBE/'classes')==read(PROBE/'class-hashes.json')
    source,observer,phase=[root/n for n in ('source','observer-classes','phase-classes')]
    for p in (source,observer,phase):p.mkdir()
    for p in (ROOT/'src/algorithms/diagnostics/gom_phase').glob('*.java'):shutil.copy2(p,source)
    raw=(PROBE/'source/GomPipelineProbe.java').read_text('utf-8-sig')
    raw=once(raw,'    private long events;', '    private long events;\n    private final GomPhasePaidDigest paid=new GomPhasePaidDigest();')
    raw=once(raw,'"points",points,"memory",memory));','"points",points,"memory",memory,"allPaid",current.scope.archive()));')
    raw=once(raw,'        if(current==null||!current.scope.lastFlags.fresh)return;',
        '        if(current==null)return;\n        current.paid.update(p,fe);\n'
        '        if(fe==223840||fe==228840)current.emit(GomRecords.row("kind","paidPrefix","sha256",current.paid.snapshot()));\n'
        '        if(!current.scope.lastFlags.fresh)return;')
    raw=once(raw,'"passes",probe.scope.completedPasses));','"passes",probe.scope.completedPasses,"paidSHA256",probe.paid.snapshot()));')
    (source/'GomPipelineProbe.java').write_text(raw,encoding='utf-8')
    canonical=(PROBE/'source/CanonicalHmopso.java').read_text('utf-8-sig')
    canonical=once(canonical,'                    Direction preference = preference(direction);','                    Direction preference = localPreference(direction);')
    old='    private Direction preference(Direction group) { return support == null ? group : support.preference(group); }'
    new='    private Direction basePreference(Direction group) { return support == null ? group : support.preference(group); }\n'
    new+='    private Direction preference(Direction group) { return GomPhasePreferences.global(basePreference(group)); }\n'
    new+='    private Direction localPreference(Direction group) { return GomPhasePreferences.local(basePreference(group)); }'
    canonical=once(canonical,old,new);(source/'CanonicalHmopso.java').write_text(canonical,encoding='utf-8')
    for name in ('ctx_phase_build.py','ctx_phase_support.py','ctx_phase_analysis.py','run_ctx_phase_role_causal.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(PROBE/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java','-version'],root/'jdk-version.log')
    java=[str(p) for p in source.glob('*.java') if p.name!='CanonicalHmopso.java']
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(observer),*java],root/'compile-observer.log')
    native=str(observer)+';'+base
    execute(['javac','-encoding','UTF-8','--release','8','-cp',native,'-d',str(phase),str(source/'CanonicalHmopso.java')],root/'compile-phase.log')
    changed=str(phase)+';'+native
    for name,cp in (('native-classpath.txt',native),('classpath.txt',changed)):(root/name).write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json',dict(observer=class_hashes(observer),phase=class_hashes(phase)))
    write_once(root/'original-source-identities.json',{str(PROBE/'source'/n):digest(PROBE/'source'/n) for n in ('CanonicalHmopso.java','GomPipelineProbe.java')})
    return native,changed

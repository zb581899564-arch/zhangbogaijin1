"""Resolve actual frozen classes, then shadow only LocalSearch observer hooks and the frozen entry."""
from pathlib import Path
from urllib.parse import unquote,urlparse
import shutil
from run_long_budget_bridge import ROOT, read, write_once, execute
from paired_survival_bench import class_hashes
from run_paired_qgs_guidance import replace

SOURCE=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
PREFIX='org.uma.jmetal.util.research.search.'


def resolve(root,cp):
    out=root/'original-identity';classes=out/'classes';classes.mkdir(parents=True)
    java=ROOT/'src/algorithms/diagnostics/ClassResolutionProbe.java';shutil.copy2(java,out)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(out/java.name)],out/'compile.log')
    names=[PREFIX+k for k in ('LocalSearch','SearchState','QgsLocalLedger','IntraNeighborhoods')]
    execute(['java','-cp',f'{classes};{cp}','research.dynamic.ClassResolutionProbe',*names],out/'classes.json')
    identity=read(out/'classes.json');parsed=unquote(urlparse(identity[PREFIX+'LocalSearch']['codeSource']).path)
    if parsed.startswith('/') and len(parsed)>2 and parsed[2]==':':parsed=parsed[1:]
    source=Path(parsed).parent/'source/LocalSearch.java'
    assert source.is_file() and source.is_relative_to(ROOT/'runs'),source
    write_once(out/'local-source.json',{'source':str(source)})
    execute(['E:/javavava/bin/javap.exe','-classpath',cp,'-c','-p',PREFIX+'IntraNeighborhoods'],out/'IntraNeighborhoods.javap.txt')
    execute(['E:/javavava/bin/javap.exe','-classpath',cp,'-c','-p',PREFIX+'QgsLocalLedger'],out/'QgsLocalLedger.javap.txt')
    return source


def build(root):
    base=(SOURCE/'classpath.txt').read_text('utf-8');original=resolve(root,base)
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    local=original.read_text('utf-8')
    local=replace(local,'        QgsLocalLedger.Slot slot = ledger.inter(state.ledgerGroup(direction));',
        '        QgsLocalLedger.Slot slot = ledger.inter(state.ledgerGroup(direction));\n        CriticalSlotAudit.visitStarted(slot.group);')
    local=replace(local,'                int[] remaining = {slot.limit};\n                try {',
        '                int[] remaining = {slot.limit};\n                CriticalSlotAudit.begin(current, direction, slot, factory);\n'
        '                boolean slotReturned = false;\n                try {')
    local=replace(local,'                    } while (slot.fixed && remaining[0] > 0);',
        '                    } while (slot.fixed && remaining[0] > 0);\n                    slotReturned = true;')
    local=replace(local,'                    slot.paid = slot.limit - remaining[0];\n                    ledger.end(slot);',
        '                    slot.paid = slot.limit - remaining[0];\n                    CriticalSlotAudit.end(current, slot, slotReturned);\n                    ledger.end(slot);')
    entry=(SOURCE/'source/PddrIsolationRun.java').read_text('utf-8')
    entry=replace(entry,'        context.problem().setObserver(obs);',
        '        context.problem().setObserver(obs);\n        org.uma.jmetal.util.research.search.CriticalSlotAudit.output(out);')
    entry=replace(entry,'            throw failure;',
        '            org.uma.jmetal.util.research.search.CriticalSlotAudit.failureEvidence(out, failure.toString(), '
        'context.budget().attempted(), context.budget().successful(), context.budget().failed());\n            throw failure;')
    entry=replace(entry,'            if (digest != null) digest.update(paid, s);',
        '            if (digest != null) digest.update(paid, s);\n            org.uma.jmetal.util.research.search.CriticalSlotAudit.paid(s, paid, changed, archive);')
    entry=replace(entry,'        obs.write(out);',
        '        obs.write(out);\n        org.uma.jmetal.util.research.search.CriticalSlotAudit.finish(out);')
    (source/'LocalSearch.java').write_text(local,encoding='utf-8');(source/'PddrIsolationRun.java').write_text(entry,encoding='utf-8')
    for name in ('CriticalSlotCertificate','CriticalSlotAudit','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('critical_slot_build.py','critical_slot_analysis.py','run_critical_slot_audit.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    shutil.copytree(ROOT/'research/composition_oracle',source/'composition_oracle',ignore=shutil.ignore_patterns('__pycache__'))
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8')
    execute(['java','-cp',cp,'research.dynamic.ClassResolutionProbe',PREFIX+'LocalSearch',PREFIX+'SearchState',PREFIX+'QgsLocalLedger',
             PREFIX+'IntraNeighborhoods',PREFIX+'CriticalSlotAudit'],root/'loaded-identity.json')
    return cp

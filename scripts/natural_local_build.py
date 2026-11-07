"""Reuse the accepted true-deadline entry and search binaries, adding explicit record/replay selection only."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, execute, write_once
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes

ENTRY=ROOT/'runs/snapshot-time-audit-20261105-052055-989426'
FROZEN=ROOT/'runs/makespan-tie-screen-20261105-025223-471920'


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    body=(ENTRY/'source/SnapshotTimeRun.java').read_text('utf-8')
    body=replace(body,'public final class SnapshotTimeRun {','public final class NaturalLocalRun {')
    body=replace(body,'    private SnapshotTimeRun() { }','    private NaturalLocalRun() { }')
    body=replace(body,'        final PddrPaidDigest digest; final List<Map<String,Object>> initial=new ArrayList<>();',
        '        final PddrPaidDigest digest; final List<Map<String,Object>> initial=new ArrayList<>();\n        final NaturalRunEvidence lastPaid=new NaturalRunEvidence();')
    body=replace(body,'new double[]{.5,1},CHECKS);','new double[]{.5,1},NaturalRunEvidence.checkpoints(limit));')
    body=replace(body,'            if(digest!=null)digest.update(fe,(PermutationSolution<?>)value);',
        '            lastPaid.observed(archive,fe);\n            if(digest!=null)digest.update(fe,(PermutationSolution<?>)value);')
    body=replace(body,'            genomes.completedSolution(value,fe,seconds,changed,archive);',
        '            genomes.completedSolution(value,fe,seconds,changed,archive);\n            lastPaid.maybeInject(fe);')
    body=replace(body,'        System.setProperty("research.qgsAudit.mode","replay");System.setProperty("research.qgsAudit.ledger",args[8]);',
        '        String regime=args[9];if(!Arrays.asList("record","replay").contains(regime))throw new IllegalArgumentException("Unknown local regime");\n'
        '        System.setProperty("research.qgsAudit.mode",regime);System.setProperty("research.qgsAudit.ledger",args[8]);')
    body=replace(body,'        Evidence evidence=new Evidence(limit,seconds);context.problem().setObserver(evidence);',
        '        Evidence evidence=new Evidence(limit,seconds);context.problem().setObserver(evidence);\n        NaturalRunEvidence.identity(out);')
    body=replace(body,'        Map<String,Object> receipt=row("mode",mode,"seed",seed,"stopReason",context.stopReason(),',
        '        Map<String,Object> receipt=row("mode",mode,"seed",seed,"localLedgerMode",regime,"searchConfiguration",search.configuration,"stopReason",context.stopReason(),')
    body=replace(body,'        if(failure!=null)throw new IllegalStateException("True-deadline run failed; fee receipt retained",failure);',
        '        if(failure!=null) {\n            evidence.lastPaid.writeFailure(out,failure.toString(),context.budget().attempted(),context.budget().successful(),context.budget().failed());\n'
        '            throw new IllegalStateException("Natural/replay run failed; receipt and available front retained",failure);\n        }')
    (source/'NaturalLocalRun.java').write_text(body,encoding='utf-8')
    for name in ('NaturalRunEvidence','NaturalLedgerChecks','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('natural_local_build.py','natural_local_support.py','run_natural_local_audit.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(ENTRY/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp

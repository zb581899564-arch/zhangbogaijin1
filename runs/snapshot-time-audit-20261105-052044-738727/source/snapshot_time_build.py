"""Deadline-only ledger finalization; before the deadline and with infinite T the frozen rules remain exact."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, execute, write_once
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from run_snapshot_anchor_audit import SOURCE


def ledger_source():
    body=(SOURCE/'source/QgsLocalLedger.java').read_text('utf-8')
    body=replace(body,'    private static QgsLocalLedger active;',
        '''    private static QgsLocalLedger active;
    private static java.util.function.BooleanSupplier deadline;
    public static void allowDeadlinePrefix(java.util.function.BooleanSupplier value) { deadline = value; }
    private static boolean deadlineReached() { return deadline != null && deadline.getAsBoolean(); }''')
    body=replace(body,'if (slot.fixed && slot.paid != slot.limit) throw',
        'if (slot.fixed && slot.paid != slot.limit && !deadlineReached()) throw')
    body=replace(body,'if (self.replay && self.index != self.expected.size()) throw',
        'if (self.replay && self.index != self.expected.size() && !deadlineReached()) throw')
    return body


def build(root,base_cp):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    (source/'QgsLocalLedger.java').write_text(ledger_source(),encoding='utf-8')
    for name in ('SnapshotTimeRun','DeadlineLedgerChecks','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('snapshot_time_build.py','snapshot_time_support.py','run_snapshot_time_audit.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base_cp,'-d',str(classes),
             *map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes))
    cp=f'{classes};{base_cp}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
    return cp

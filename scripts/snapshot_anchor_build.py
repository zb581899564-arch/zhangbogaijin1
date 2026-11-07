"""Shadow only the archive snapshot helper and its read-only receipt hooks in an isolated classpath."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, execute, write_once
from paired_survival_bench import FROZEN, class_hashes
from run_paired_qgs_guidance import replace


def snapshot_source():
    body = (FROZEN/'source/src/java/runtime/SolutionSnapshots.java').read_text('utf-8')
    body = replace(body, '    static <S extends Solution<?>> S copy(S solution) {',
        '''    private static <S extends Solution<?>> S serialCopy(S solution) {''')
    body = replace(body, '            try (ObjectInputStream input = new ObjectInputStream(',
        '            SnapshotCopyMetrics.serialized(bytes.size(), 0);\n            try (ObjectInputStream input = new ObjectInputStream(')
    return replace(body, '    private SolutionSnapshots() { }', '''    private SolutionSnapshots() { }
    private static final String MODE = System.getProperty("research.snapshot.mode", "SERIAL");
    static {
        if (!MODE.equals("SERIAL") && !MODE.equals("ANCHOR"))
            throw new IllegalArgumentException("Unknown isolated snapshot mode: " + MODE);
    }
    static <S extends Solution<?>> S copy(S solution) {
        long start = SnapshotCopyMetrics.begin();
        try { return MODE.equals("ANCHOR") ? AnchoredSnapshotGraph.copy(solution) : serialCopy(solution); }
        finally { SnapshotCopyMetrics.end(start); }
    }''')


def build(root, source_run, cp):
    source, classes = root/'source', root/'classes'
    source.mkdir(); classes.mkdir()
    (source/'SolutionSnapshots.java').write_text(snapshot_source(), encoding='utf-8')
    entry = (source_run/'source/PddrIsolationRun.java').read_text('utf-8')
    entry = replace(entry, '        try { context.run(search.algorithm); }',
        '        try { org.uma.jmetal.util.research.runtime.SnapshotCopyMetrics.searchStarted(); context.run(search.algorithm); }')
    entry = replace(entry, '        } finally { dynamic.clearPrepared(); }',
        '        } finally { org.uma.jmetal.util.research.runtime.SnapshotCopyMetrics.searchEnded(); dynamic.clearPrepared(); }')
    entry = replace(entry, '        DynamicOutput.write(out, in, params, context.result(), receipt, false);',
        '        DynamicOutput.write(out, in, params, context.result(), receipt, false);\n'
        '        append(out.resolve("copy-metrics.jsonl"), org.uma.jmetal.util.research.runtime.SnapshotCopyMetrics.snapshot());')
    (source/'PddrIsolationRun.java').write_text(entry, encoding='utf-8')
    for name in ('AnchoredSnapshotGraph','SnapshotCopyMetrics','SnapshotContractData','SnapshotContractChecks','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('snapshot_anchor_build.py','run_snapshot_anchor_audit.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),
             *map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes))
    cp=f'{classes};{cp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8')
    return cp

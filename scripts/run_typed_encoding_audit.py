"""Engineering-only typed representation, exact replay of 400 existing paid sources; zero search FE."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

SOURCE = ROOT / 'runs/linkage-mixing-probe-20261105-142116-487815'
BASE = ROOT / 'runs/schedule-factor-probe-20261105-124946-994085'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)


def build(root):
    source, classes = root / 'source', root / 'classes'
    source.mkdir(); classes.mkdir()
    for folder in ('src/algorithms/model_global/encoding', 'src/algorithms/diagnostics/typed_encoding'):
        for path in (ROOT / folder).glob('*.java'):
            shutil.copy2(path, source)
    for path in (BASE / 'source/NeutralProbeSupport.java', ROOT / 'src/java/dynamicentries/ProbeData.java', Path(__file__)):
        shutil.copy2(path, source)
    base = (BASE / 'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}'
    (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    return cp


def totals(root):
    receipts = [r for p in root.glob('*/*/audit/receipt.jsonl') for r in rows(p)]
    return {key: sum(r[key] for r in receipts) for key in (
        'optimizationFE', 'decoderCalls', 'sourceGenomes', 'exactTimelinePairs', 'pureChecks', 'expectedMalformedRejections')}


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        assert read(SOURCE / 'status.json')['status'] == 'COMPLETE'
        root = ROOT / 'runs' / datetime.now().strftime('typed-encoding-audit-%Y%m%d-%H%M%S-%f')
        root.mkdir(); print('TYPED_ENCODING_AUDIT_ROOT', root, flush=True)
        write_once(root / 'protocol.json', {
            'purpose': 'Exact expressive representation and legality audit, no algorithm or performance claim',
            'source': str(SOURCE), 'instances': STEMS, 'sourceSeeds': SEEDS,
            'representation': 'By-job first-stage legal categorical (F,M,W) ids plus separate finite global priority keys in closed [0,1]',
            'roundtrip': 'Preserve all four raw positional vectors, including neutral global interleaving; no repair/canonicalization',
            'keyTies': 'Ascending key, descending job id on equality, including signed zero; matches original strict-< right-biased merge',
            'keys': 'Default (rank+.5)/N; random strictly sorted reencoding with 0 and 1 endpoints preserves global order',
            'legality': 'Reject repeated/out-of-range jobs, tuple/resource ids, wrong lengths, missing factories and invalid keys; immutable inputs',
            'qa': '400 existing known source encodings, original objectives bit-exact, full original versus roundtrip timeline all identifiers/10numeric fields',
            'expectedDecoderCalls': 800, 'optimizationFE': 0,
            'paidSearchRuleUnchanged': 'Every generated search attempt still must pass RunContext; these are explicit offline QA replays only',
            'fixedFaMiProgramStopUnchanged': True, 'defaultMainlineChanged': False,
            'externalTransfersThisAudit': False, 'fullGomeaImplemented': False, 'goalAchieved': False})
        try:
            cp = build(root)
            for stem in STEMS:
                for seed in SEEDS:
                    folder = root / stem / str(seed); folder.mkdir(parents=True)
                    inputs = SOURCE / stem / 'inputs'
                    source = SOURCE / stem / str(seed) / 'sources.tsv'
                    files = [source, inputs / f'{stem}.txt', inputs / 'RECONSTRUCTED-setup.txt', inputs / 'fatigue-input.txt']
                    write_once(folder / 'input-hashes.json', {str(p): digest(p) for p in files})
                    command = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.TypedEncodingRun',
                               str(files[1]), str(files[2]), str(files[3]), str(source), str(folder / 'audit'), str(13510003 + seed)]
                    write_once(folder / 'command.json', command)
                    print('TYPED_ENCODING_CONTEXT', stem, seed, flush=True)
                    execute(command, folder / 'run.log', timeout=120)
                    receipt, = rows(folder / 'audit/receipt.jsonl')
                    assert receipt['status'] == 'COMPLETE' and receipt['optimizationFE'] == 0
            actual = totals(root)
            assert actual['decoderCalls'] == 800 and actual['sourceGenomes'] == actual['exactTimelinePairs'] == 400
            assert actual['expectedMalformedRejections'] == 5200
            write_once(root / 'analysis.json', {'allContractsPass': True, **actual,
                'performanceEvidence': False, 'fullGomeaImplemented': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **totals(root)})
            raise
        write_once(root / 'status.json', {'status': 'COMPLETE', **actual, 'goalAchieved': False})
        print('TYPED_ENCODING_AUDIT_COMPLETE', actual, flush=True)


if __name__ == '__main__':
    main()

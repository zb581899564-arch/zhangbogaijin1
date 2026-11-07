"""Paper-grounded joint model and physical per-factory reencoding QA; zero new search FE."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from pa_model_audit_analysis import analyze

SOURCE = ROOT / 'runs/linkage-mixing-probe-20261105-142116-487815'
BASE = ROOT / 'runs/schedule-factor-probe-20261105-124946-994085'
PAPER = ROOT / 'research/gomea_reference_audit/private-publications-20261105-155034-012023'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)


def build(root):
    source, classes = root / 'source', root / 'classes'; source.mkdir(); classes.mkdir()
    for folder in ('src/algorithms/model_global/encoding', 'src/algorithms/model_global/linkage', 'src/algorithms/diagnostics/pa_model'):
        for path in (ROOT / folder).glob('*.java'):
            shutil.copy2(path, source)
    for path in (BASE / 'source/NeutralProbeSupport.java', ROOT / 'src/java/dynamicentries/ProbeData.java', Path(__file__), Path(__file__).with_name('pa_model_audit_analysis.py')):
        shutil.copy2(path, source)
    base = (BASE / 'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}'; (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes)); write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    return cp


def fees(root):
    receipts = [r for path in root.glob('*/*/audit/receipt.jsonl') for r in rows(path)]
    return {k: sum(r[k] for r in receipts) for k in ('optimizationFE', 'decoderCalls', 'sourceGenomes', 'neutralViewExactKeyMatches', 'rawGlobalOrderChanges', 'componentPairs')}


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        assert read(SOURCE / 'status.json')['status'] == read(PAPER / 'status.json')['status'] == 'COMPLETE'
        root = ROOT / 'runs' / datetime.now().strftime('pa-model-audit-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('PA_MODEL_AUDIT_ROOT', root, flush=True); contexts = []
        write_once(root / 'protocol.json', {
            'purpose': 'Independent implementation of author thesisChapter3 joint dependency and per-factory reencoding, no evolving optimizer yet',
            'sourcePaper': read(PAPER / 'manifest.json'), 'visualFormulaPages': [70, 71, 72, 73, 75, 76],
            'formula': 'Eq3.14-3.19, map shift=factory, all jobs eligible for all factories, pi=1/F; published weight2/3',
            'nullModelLimit': 'Hypothetical independent uniform assignment, not calibrated to our nonempty/conditioned initialization or protected families',
            'resources': 'Machine/worker remain legal complete job tuples, not learned as separate dependence variables in this factory-order model',
            'reencoding': 'Fresh open(0,1) keys sorted/reassigned independently per factory; retain complete FMW and physical chains; global interleaving may change',
            'finiteRng': 'Zero endpoint or within-factory duplicate causes retained engineering failure, no hidden redraw',
            'neutralControl': 'Reverse factory-concatenated raw view with identical RNG yields bit-identical by-job resources and keys',
            'hierarchy': 'Average linkage via weighted mean updates; exact-double score then lexicographic cluster tie; includes all2N-1subsets; O(N^2logN) queue adaptation',
            'independentQA': 'Scipy binomial CDF/SF, H(A)+H(B)-H(A,B) MI, original-matrix mean-cluster maxima, degenerate/symmetric cases',
            'scope': '2existing developmentinstances x2old source seeds x80free paid sources; no source-search rerun, model output not used to select candidates',
            'expectedFullDecoderQA': 640, 'optimizationFE': 0, 'oldFaMiProgramStopUnchanged': True,
            'defaultMainlineChanged': False, 'externalTransferThisAudit': False, 'goalAchieved': False})
        try:
            cp = build(root)
            for stem in STEMS:
                for seed in SEEDS:
                    folder = root / stem / str(seed); folder.mkdir(parents=True); inputs = SOURCE / stem / 'inputs'
                    source = SOURCE / stem / str(seed) / 'sources.tsv'
                    files = [inputs / f'{stem}.txt', inputs / 'RECONSTRUCTED-setup.txt', inputs / 'fatigue-input.txt', source]
                    write_once(folder / 'input-hashes.json', {str(p): digest(p) for p in files})
                    command = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.PaModelAuditRun',
                               *map(str, files), str(folder / 'audit'), str(13530003 + seed)]
                    write_once(folder / 'command.json', command); print('PA_MODEL_CONTEXT', stem, seed, flush=True)
                    execute(command, folder / 'run.log', timeout=120)
                    result = analyze(folder / 'audit'); result.update(stem=stem, seed=seed); contexts.append(result)
            actual = fees(root)
            assert actual['decoderCalls'] == 640 and actual['sourceGenomes'] == actual['neutralViewExactKeyMatches'] == 320
            assert actual['componentPairs'] == 10280 and actual['optimizationFE'] == 0
            write_once(root / 'analysis.json', {'contexts': contexts, **actual, 'allEngineeringChecksPass': True,
                'newOptimizerImplemented': False, 'performanceEvidence': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root)})
            raise
        write_once(root / 'status.json', {'status': 'COMPLETE', **actual, 'goalAchieved': False})
        print('PA_MODEL_AUDIT_COMPLETE', actual, flush=True)


if __name__ == '__main__':
    main()

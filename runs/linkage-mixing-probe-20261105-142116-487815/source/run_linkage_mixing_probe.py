"""Isolated complete mixing programs, model/representation checks before evaluation, no mainline change."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from linkage_mixing_design import SOURCE, BASE, STEMS, protocol, prepare
from linkage_mixing_analysis import analyze


def build(root):
    source, classes = root / 'source', root / 'classes';source.mkdir();classes.mkdir()
    for path in (ROOT / 'src/algorithms/diagnostics/linkage_mixing').glob('*.java'): shutil.copy2(path, source)
    for path in (BASE / 'source/NeutralProbeSupport.java', ROOT / 'src/java/dynamicentries/ProbeData.java'):
        shutil.copy2(path, source)
    for name in ('linkage_mixing_design.py', 'linkage_mixing_analysis.py', 'run_linkage_mixing_probe.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (BASE / 'classpath.txt').read_text('utf-8-sig').strip();execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes));write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.glob('*')})
    return cp


def model_checks(root, stem, contexts):
    import math
    from collections import Counter
    from linkage_mixing_design import source_pool
    from gap_structure_sources import by_job
    import numpy as np
    worst = 0.;pairs = 0
    def entropy(values):
        counts = Counter(values);n = len(values)
        return -sum((c / n) * math.log(c / n) for c in counts.values())
    for context in contexts:
        _, groups, _ = source_pool(stem, context['seed']);matrix = np.asarray([by_job(p)[:, 0] for values in groups.values() for p in values])
        model = read(root / stem / str(context['seed']) / 'model.json')
        for i in range(matrix.shape[1]):
            for j in range(i):
                independent = entropy(matrix[:, i]) + entropy(matrix[:, j]) - entropy(list(zip(matrix[:, i], matrix[:, j])))
                error = abs(independent - model['mutualInformation'][i][j]);worst = max(worst, error);assert error < 1e-12;pairs += 1
        assert sorted(model['randomRelabel']) == list(range(matrix.shape[1]))
    write_once(root / stem / 'model-acceptance.json', {'status': 'PASS', 'independentEntropyIdentityPairs': pairs,
        'maxAbsoluteMIerror': worst, 'sourceGenesNeutralInterleavingInvariantByJob': True, 'searchFE': 0, 'decoderCalls': 0})


def fees(root):
    receipts = [rows(p)[0] for p in root.glob('*/*/probe/receipt.jsonl')]
    return {'successfulFE': sum(r['successfulFE'] for r in receipts), 'attemptedFE': sum(r['attemptedFE'] for r in receipts),
        'failedFE': sum(r['failedFE'] for r in receipts), 'fullDecoderQA': sum(r['fullDecoderQA'] for r in receipts),
        'pureGenomeContractChecks': sum(r['pureGenomeContractChecks'] for r in receipts)}


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        assert read(SOURCE / 'status.json')['status'] == 'COMPLETE'
        root = ROOT / 'runs' / datetime.now().strftime('linkage-mixing-probe-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('LINKAGE_MIXING_ROOT', root, flush=True);results = []
        try:
            plan = protocol();write_once(root / 'protocol.json', plan);contexts = {}
            for stem in STEMS:
                contexts[stem] = prepare(root, stem);model_checks(root, stem, contexts[stem])
            assert sum(c['expectedSuccessfulFE'] for values in contexts.values() for c in values) == 61328
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p) for stem in STEMS for p in (root / stem).rglob('*') if p.is_file()})
            cp = build(root);specs = {s['stem']: s for s in plan['instances']}
            for stem in STEMS:
                for case in contexts[stem]:
                    folder = root / stem / str(case['seed']);inp = root / stem / 'inputs'
                    cmd = ['java', '-Xms32m', '-Xmx2g', '-Dresearch.snapshot.mode=ANCHOR', '-cp', cp, 'research.dynamic.LinkageMixingRun',
                        str(inp / f'{stem}.txt'), str(inp / 'RECONSTRUCTED-setup.txt'), str(inp / 'fatigue-input.txt'),
                        str(folder), str(folder / 'probe'), str(case['noiseSeed'])]
                    write_once(folder / 'command.json', cmd);print('LINKAGE_MIXING_RUN', stem, case['seed'], case['expectedSuccessfulFE'], flush=True)
                    execute(cmd, folder / 'run.log', timeout=300)
                    receipt, = rows(folder / 'probe/receipt.jsonl')
                    assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['fullDecoderQA'] == case['expectedSuccessfulFE'] and receipt['failedFE'] == 0
                results.append(analyze(root, specs[stem]))
            passed = all(r['pass'] for r in results)
            write_once(root / 'analysis.json', {'instances': results, 'worthEvolvingPopulationProtocol': passed,
                'decision': 'DESIGN_EVOLVING_POPULATION_COMPARISON' if passed else 'STOP_FIXED_FA_MI_RANK_DONATION_PROGRAM',
                'newFullAlgorithmImplemented': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root)});raise
        actual = fees(root);assert actual['successfulFE'] == actual['attemptedFE'] == actual['fullDecoderQA'] == 61328
        write_once(root / 'status.json', {'status': 'COMPLETE', **actual, 'worthEvolvingPopulationProtocol': passed,
            'defaultMainlineChanged': False, 'goalAchieved': False})
        print('LINKAGE_MIXING_COMPLETE', passed, actual, flush=True)


if __name__ == '__main__': main()

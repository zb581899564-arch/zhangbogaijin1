"""Close the natural receiver suffix after the failed one-step probe; no mechanism promotion."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock, nondominated, hypervolume, igd_plus
from pa_neutral_suffix_support import split_cases, extract, write_program, validate_branch
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage

PRIOR = ROOT/'runs/pa-neutral-relay-probe-20261106-033038-764322'


def metrics(a, b, norm):
    normalize = lambda x: (np.asarray(x, float).reshape(-1, 3)-norm['lower'])/norm['scale']
    reference = nondominated(normalize(a+b)); aa, bb = normalize(a), normalize(b)
    ia, ib = igd_plus(aa, reference), igd_plus(bb, reference)
    hv = {str(r): {'actual': hypervolume(aa, (r,)*3), 'rollback': hypervolume(bb, (r,)*3)} for r in (1.25, 1.5, 2.)}
    return {'HV': hv, 'IGDplusActual': ia, 'IGDplusRollback': ib,
            'IGDplusSymmetricWorseningPct': 200*(ia-ib)/(ia+ib) if ia+ib else 0., 'coverage': bidirectional_coverage(a, b)}


def fees(root):
    receipts = [rows(p)[0] for p in root.glob('*/*/*/receipt.jsonl')]
    return {'runs': len(receipts), **{key: sum(r[key] for r in receipts) for key in ('successfulFE', 'attemptedFE', 'failedFE', 'paidFullTimelineQA')}}


def build(root):
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    shutil.copy2(ROOT/'src/algorithms/diagnostics/pa_neutral/PaFixedSuffixRun.java', source)
    for name in ('run_pa_neutral_suffix_closure.py', 'pa_neutral_suffix_support.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (PRIOR/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), str(source/'PaFixedSuffixRun.java')], root/'compile.log')
    cp = str(classes)+';'+base; (root/'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root/'class-hashes.json', class_hashes(classes)); write_once(root/'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    return cp


def run_branch(root, cp, stem, block, branch, catalog):
    out = root/stem/str(block['case'])/branch; expected = write_program(out, block, branch, catalog['tuples']); inp = root/stem/'inputs'
    cmd = ['java', '-Xms32m', '-Xmx2g', '-Dresearch.snapshot.mode=ANCHOR', '-cp', cp, 'research.dynamic.PaFixedSuffixRun',
           str(inp/(stem+'.txt')), str(inp/'RECONSTRUCTED-setup.txt'), str(inp/'fatigue-input.txt'), str(out/'program.tsv'),
           str(out/'prior-archive.tsv'), str(out), branch]
    write_once(out/'command.json', cmd); print('PA_NEUTRAL_SUFFIX', stem, block['case'], branch, expected, flush=True)
    execute(cmd, out/'run.log', timeout=180)
    result = validate_branch(out, block, branch, catalog['tuples'])
    capture, = rows(out/'loaded-identity.jsonl'); write_once(out/'identity-verified.json', verify_capture(capture, cp))
    return result


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        assert read(PRIOR/'status.json')['decision'] == 'STOP_LATEST_NEUTRAL_RELAY_HYPOTHESIS'
        root = ROOT/'runs'/datetime.now().strftime('pa-neutral-suffix-closure-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('PA_NEUTRAL_SUFFIX_ROOT', root, flush=True)
        specs = read(PRIOR/'protocol.json')['instances']; prepared = []; blocks_by_stem = {}; catalogs = {}; before = protected()
        for spec in specs:
            stem = spec['stem']; needed, pruned = split_cases(PRIOR/stem)
            assert len(needed)+len(pruned) == 24
            prepared.append({'stem': stem, 'neededCases': [c['case'] for c in needed], 'pruned': pruned})
            blocks_by_stem[stem], catalogs[stem] = extract(PRIOR/stem, needed)
        assert sum(len(v) for v in blocks_by_stem.values()) == 3 and sum(len(p['pruned']) for p in prepared) == 45
        expected_total = sum(2*(2+len(b['moves'])) for blocks in blocks_by_stem.values() for b in blocks)
        write_once(root/'protocol.json', {'version': 'NEUTRAL_RECEIVER_NATURAL_SUFFIX_CLOSURE-v1', 'registered': '2026-11-06',
            'source': str(PRIOR), 'contexts': prepared, 'maximumActualSearchFE': 560, 'actualFrozenActionsFE': expected_total,
            'question': 'Does the same original receiver program reveal delayed effects in the3nonidenticalpostfork states?',
            'pruning': '45pairs have exact equal genotype/objectives and internalarchive afteracceptance, so the same deterministic remainingactions are identical; no physical-only equivalence shortcut',
            'fixed': 'Same original receiver, model, ordered remainingFOS and actual donors until its original programEnd. No extra generations, seeds, windows or new donor choices. Parent andfork re-evaluated in BOTHbranches; every remaining attempt paid',
            'verification': 'ACTUAL everypaid childrawhash/genome/objective/finalworking/archive matches frozen source; independent reconstruction of BOTHbranches and fulltimelineQA everypoint',
            'indicators': 'Common source priorarchive union eachbranchpaid suffix; priornorm, HV1.5/1.25/2, IGD+NDunionofbothfronts, exactbidirectionalweakC',
            'interpretation': 'Conditional causal closure, not another performance screen. Preserve failed one-step decision regardless of outcome; no algorithm/selector promotion or budget extension',
            'defaultMainlineChanged': False, 'goalAchieved': False})
        write_once(root/'source-blocks.json', blocks_by_stem); write_once(root/'protected-before.json', before)
        try:
            cp = build(root); results = []
            for spec in specs:
                stem = spec['stem']; shutil.copytree(PRIOR/stem/'inputs', root/stem/'inputs')
                for block in blocks_by_stem[stem]:
                    a = run_branch(root, cp, stem, block, 'ACTUAL', catalogs[stem])
                    b = run_branch(root, cp, stem, block, 'ROLLBACK', catalogs[stem])
                    result = {'stem': stem, 'case': block['case'], 'sourceFE': block['paidFE'], 'remainingMoves': len(block['moves']),
                        'sameEndGenome': a['lastResources'] == b['lastResources'] and a['lastKeys'] == b['lastKeys'],
                        'sameEndObjectives': a['lastWorking']['objectives'] == b['lastWorking']['objectives'],
                        'sameEndArchive': a['internalArchive'] == b['internalArchive'], **metrics(a['internalArchive'], b['internalArchive'], spec['normalization'])}
                    results.append(result)
            actual = fees(root)
            assert actual['successfulFE'] == actual['attemptedFE'] == actual['paidFullTimelineQA'] == expected_total <= 560 and actual['failedFE'] == 0
            assert protected() == before and class_hashes(root/'classes') == read(root/'class-hashes.json')
            for name, sha in read(root/'source-hashes.json').items():
                assert digest(root/'source'/name) == sha
            write_once(root/'analysis.json', {'contexts': prepared, 'results': results, **actual, 'oldOneStepStopUnchanged': True,
                'mechanismPromoted': False, 'defaultMainlineChanged': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root/'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root), 'goalAchieved': False}); raise
        write_once(root/'status.json', {'status': 'COMPLETE', **actual, 'oldOneStepStopUnchanged': True, 'goalAchieved': False})
        print('PA_NEUTRAL_SUFFIX_COMPLETE', actual, results, flush=True)


if __name__ == '__main__':
    main()

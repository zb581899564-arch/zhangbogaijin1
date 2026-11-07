"""Freeze a small physical-equivalence and offspring test before any canonicalization change."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from pool_phase_build import OBS
from research.search_mechanism.campaign import _case_fields
from neutral_view_analysis import analyze

SOURCE = ROOT / 'runs/teacher-coupling-probe-20261105-011608-145831'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (10060007, 10060031)
REPS, PROBE_SEED = 16, 11490011


def prepare_cases(root, stem):
    folder = root / stem
    shutil.copytree(SOURCE / stem / 'inputs', folder / 'inputs')
    cases = []
    for seed in SEEDS:
        original = SOURCE / stem / str(seed)
        off, = rows(original / 'OFF/run-receipt.jsonl')
        on, = rows(original / 'ON/run-receipt.jsonl')
        assert off['successful'] == on['successful'] == 5100
        assert off['failed'] == on['failed'] == 0
        assert len(off['paidSHA256']) == 64 and off['paidSHA256'] == on['paidSHA256']
        assert read(original / 'ON/observation-equivalence.json')['status'] == 'PASS'
        cohort_path = original / 'ON/teacher-cohorts.jsonl'
        shutil.copy2(cohort_path, folder / f'source-cohorts-{seed}.jsonl')
        captured, = rows(cohort_path)
        assert captured['rolesCaptured'] == 4
        for cohort in captured['cohorts']:
            assert len(cohort['parents']) == 8
            for parent in sorted(cohort['parents'], key=lambda r: r['parentIndex']):
                cases.append({'caseId': f"s{seed}-{cohort['role']}-p{parent['parentIndex']}",
                    'sourceSeed': seed, 'role': cohort['role'], 'paidFE': cohort['paidFE'], 'step': cohort['step'],
                    'background': cohort['background'], 'parent': parent['parent'],
                    'personal': parent['personal'], 'global': parent['nativeLeader']})
    assert len(cases) == 64
    write_once(folder / 'cases.json', {'cases': cases, 'source': str(SOURCE)})
    lines = [_case_fields(c) for c in cases]
    (folder / 'cases.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (folder / 'engineering-case.tsv').write_text(lines[0] + '\n', encoding='utf-8')


def build(root):
    source, classes = root / 'source', root / 'classes'
    source.mkdir(); classes.mkdir()
    names = ('NeutralInterleavings', 'NeutralProbeSupport', 'NeutralViewProbe', 'ClassResolutionProbe')
    for name in names:
        shutil.copy2(ROOT / f'src/algorithms/diagnostics/{name}.java', source)
    for name in ('run_neutral_view_probe.py', 'neutral_view_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    cp = (OBS / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', cp,
             '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    cp = f'{classes};{cp}'
    (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    return cp


def run_probe(root, cp, stem, engineering):
    folder = root / stem
    out = folder / ('engineering' if engineering else 'probe')
    inp = folder / 'inputs'
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.NeutralViewProbe',
           str(inp / f'{stem}.txt'), str(inp / 'RECONSTRUCTED-setup.txt'), str(inp / 'fatigue-input.txt'),
           str(folder / ('engineering-case.tsv' if engineering else 'cases.tsv')), str(out),
           '1' if engineering else str(REPS), str(PROBE_SEED)]
    write_once(folder / ('engineering-command.json' if engineering else 'probe-command.json'), cmd)
    print('NEUTRAL_VIEW_RUN', stem, 'ENGINEERING' if engineering else 'PROBE', flush=True)
    execute(cmd, folder / ('engineering.log' if engineering else 'probe.log'), timeout=180)
    receipt, = rows(out / 'receipt.jsonl')
    assert receipt['successfulFE'] == (9 if engineering else 64 * (3 + 6 * REPS))
    assert receipt['failedFE'] == 0
    return receipt


def main():
    root = ROOT / 'runs' / datetime.now().strftime('neutral-view-probe-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('NEUTRAL_VIEW_ROOT', root, flush=True)
    engineering, completed = [], []
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            specs = [s for s in read(SOURCE / 'protocol.json')['instances'] if s['stem'] in STEMS]
            write_once(root / 'protocol.json', {
                'instances': specs, 'source': str(SOURCE), 'sourceSeeds': SEEDS, 'reps': REPS, 'probeSeed': PROBE_SEED,
                'plannedDiagnosticFE': 12672, 'plannedEngineeringFE': 18, 'newCaptureFE': 0,
                'hypothesis': 'Physically equivalent teacher JS interleavings perturb global-position QGS guidance. '
                              'Recipient-order greedy merge might reduce nuisance without changing teacher schedules.',
                'sourceScope': 'Reuse all4 first actual action2 cohorts at/after step24,8 equally spaced free parents,'
                               '2 existing development seeds per instance. No resampling by gain. These are reused development contexts, not confirmation.',
                'views': 'RAW original; RANDOM uniform interleaving of unchanged per-factory chains; ALIGNED repeatedly takes '
                         'the available donor chain head with earliest recipient position. This is a greedy linear extension,'
                         'not claimed minimum-distance quotient normalization. Both donor views reference the unmutated recipient.',
                'kernels': 'Exact loaded KernelVariants JOB_ALIGNED and CLASSIC_GLOBAL; no copied or changed kernel. '
                           'Same starting construction seed across views; repairs can advance later draws differently. '
                           'View randomness is independent, deterministic per parent/rep/teacher and identical across kernels.',
                'engineering': 'Every neutral donor view full timeline exactly equals source; self-physical aligned view '
                               'recovers recipient genotype. Raw kernel repeated constructions match, all sources immutable. '
                               'Every candidate full timeline matches charged decoder; source3 replay and all96 children per case charged.',
                'scores': 'Single-offspring HV increase over pre-batch paid archive plus all3 known inputs. Same16 candidates '
                          'per view; average all64 cases, never take best view per case. Classical results are generality controls.',
                'gate': 'Both instances: >=16/64 informative cases; QGS_ALIGNED mean addedHV >=10% over RAW and >=5% over RANDOM; '
                        'at least3/4 role means nondecreasing vsRAW, no role falls >10%. Median per-case '
                        '(view preparation+kernel+paid eval)/(RAW kernel+paid eval)<=1.10. All required; failure stops '
                        'this greedy alignment without trying reverse ranks, canonical orders or weights.',
                'limits': 'Paired offspring probe only. Context time includes offline QA, observed kernels are not full algorithms. '
                          'Pass only allows a fresh closed-loop protocol, later matching enhancements for classical baselines.',
                'literature': ['https://arxiv.org/abs/0907.3202', 'https://www.sciencedirect.com/science/article/pii/S0304397511006918'],
                'preserved': 'Original mainline, four duties, Q, fixed FA, sharing, old evidence; no public push or file transfer.'})
            for stem in STEMS:
                prepare_cases(root, stem)
            cp = build(root)
            for stem in STEMS:
                engineering.append(run_probe(root, cp, stem, True))
            for stem in STEMS:
                completed.append(run_probe(root, cp, stem, False))
            result = analyze(root)
    except BaseException as exc:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': str(exc),
            'completedEngineering': len(engineering), 'completedInstances': len(completed)})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE',
        'successfulDiagnosticFE': sum(r['successfulFE'] for r in completed),
        'successfulEngineeringFE': sum(r['successfulFE'] for r in engineering), 'failedEvaluationFE': 0,
        'candidateFullTimelineQA': sum(r['candidateFullTimelineQA'] for r in completed),
        'neutralViewFullTimelineQA': sum(r['viewFullTimelineQA'] for r in completed),
        'worthFreshClosedLoop': result['worthFreshClosedLoop']})
    print('NEUTRAL_VIEW_COMPLETE', {s['stem']: {'effects': s['qgsAlignedEffectsPct'],
        'informative': s['informativeCases'], 'cost': s['medianQgsAlignedCostVsRaw'],
        'quality': s['qualityGate']} for s in result['instances']}, flush=True)


if __name__ == '__main__':
    main()

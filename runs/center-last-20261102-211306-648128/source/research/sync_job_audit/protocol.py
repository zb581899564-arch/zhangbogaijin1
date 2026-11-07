from pathlib import Path
import copy
import random

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / 'runs/semantic-repair-20261102-130342-703425'
VARIANTS = {
    'SO_JOB': {'mode': 'BASELINE_JOB_ALIGNED', 'profile': 'SO'},
    'SYNC_JOB': {'mode': 'SYNC_JOB_ALIGNED', 'profile': 'SO'},
    'SHARE_JOB': {'mode': 'SHARE_JOB_ALIGNED', 'profile': 'SO'},
    'NSGA': {'mode': 'NSGA2_4V', 'profile': 'V2'},
}
PAIRS = (('SYNC_JOB', 'SO_JOB'), ('SHARE_JOB', 'SYNC_JOB'), ('SHARE_JOB', 'SO_JOB'),
         ('SO_JOB', 'NSGA'), ('SYNC_JOB', 'NSGA'), ('SHARE_JOB', 'NSGA'))


def make_protocol(previous):
    return {'version': 'sync-job-feedback-v1', 'instances': copy.deepcopy(previous['instances']),
        'algorithm_seeds': list(previous['algorithm_seeds']), 'model': copy.deepcopy(previous['model']),
        'variants': copy.deepcopy(VARIANTS), 'runs': 120, 'planned_search_seconds': 1040,
        'wall_cap_seconds': 2700, 'one_jvm_at_a_time': True, 'classic_setting': 0,
        'main_endpoints': ['SYNC_JOB/SO_JOB organization effect', 'SHARE_JOB/SYNC_JOB sharing increment',
                           'SHARE_JOB/SO_JOB total configuration effect'],
        'locked': 'Same JOB_ALIGNED, four target groups, QGS50/alpha1/gamma0.8/exploration0.8, localCap30,200-pool PDDR, original FA family80+4x5/compose/feedback; no strategy update',
        'feedback_observer': 'All4 paid callbacks stamp private paid-FE metadata; internal offers/refresh epochs and action2 teacher age observed only; no extra FE/RNG/archive admission',
        'feedback_scope': 'Paid snapshot occurrence (not first discovery of a genotype); first offers/insertions deduplicated by paidFE; external admission counts include transient front events; absence by cutoff is censored, not proof of permanent loss',
        'feedback_capture': 'First2+last completed generations plus partial, sampled QGS steps1/10/25/50; numeric only; NSGA internal-QGS timing not applicable',
        'same_time': 'T includes initialization, all search stages, shared pools, repair, archives, old and new observation costs; JVM/input/config/offline replay/export in process and campaign wall separately',
        'fe_checkpoints': [15000], 'time_fractions': [.5, 1.],
        'metrics': {'primary_reference': [1.5]*3, 'sensitivity_references': [[1.25]*3, [2.]*3],
                    'igdplus_reference': 'Per-instance ND union of all4 methods x all5 seeds final deadline-valid fronts; approximate, offline only',
                    'aggregation': 'Five seeds averaged within each instance, then six instances equally',
                    'practical_win': '>=1% instance mean and>=3/5 seed differences positive; symmetric losses; not statistical significance'},
        'scope': 'Development attribution only, no automatic new mechanism, parameter tuning or formal step6',
        'continuation': 'Complete120 before quality interpretation unless correctness/resource failure/original45min deadline; no quality-based extra runs'}


def jobs(protocol):
    rng = random.Random(202611024); output = []
    for row in protocol['instances']:
        for seed in protocol['algorithm_seeds']:
            labels = list(VARIANTS); rng.shuffle(labels)
            for label in labels:
                output.append({'phase': 'audit', 'instance': row['stem'], 'seed': seed,
                               'variant': label, 'seconds': row['time_seconds']})
    if len(output) != protocol['runs']: raise ValueError('Complete6x5x4 required')
    return output


def trial_folder(root, job):
    return root / 'trials' / job['phase'] / job['instance'] / str(job['seed']) / job['variant']

from pathlib import Path
import copy
import random

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / 'runs/semantic-repair-20261102-130342-703425'
VARIANTS = {
    'SYNC_ORIGINAL': {'mode': 'SYNC_JOB_ALIGNED', 'profile': 'SO'},
    'SYNC_LAST': {'mode': 'SYNC_JOB_ALIGNED_CENTER_LAST', 'profile': 'SO'},
    'SHARE_ORIGINAL': {'mode': 'SHARE_JOB_ALIGNED', 'profile': 'SO'},
    'SHARE_LAST': {'mode': 'SHARE_JOB_ALIGNED_CENTER_LAST', 'profile': 'SO'},
    'NSGA': {'mode': 'NSGA2_4V', 'profile': 'V2'},
}
PAIRS = (('SYNC_LAST', 'SYNC_ORIGINAL'), ('SHARE_LAST', 'SHARE_ORIGINAL'),
         ('SHARE_ORIGINAL', 'SYNC_ORIGINAL'), ('SHARE_LAST', 'SYNC_LAST'),
         ('SYNC_ORIGINAL', 'NSGA'), ('SYNC_LAST', 'NSGA'), ('SHARE_ORIGINAL', 'NSGA'), ('SHARE_LAST', 'NSGA'))
ORIGINAL = 'MAKESPAN,CENTER,ENERGY,WORKER_COST'
LAST = 'MAKESPAN,ENERGY,WORKER_COST,CENTER'


def make_protocol(previous):
    return {'version': 'center-last-v1', 'instances': copy.deepcopy(previous['instances']),
        'algorithm_seeds': list(previous['algorithm_seeds']), 'model': copy.deepcopy(previous['model']),
        'variants': copy.deepcopy(VARIANTS), 'runs': 150, 'planned_search_seconds': 1300, 'wall_cap_seconds': 2700,
        'one_jvm_at_a_time': True, 'classic_setting': 0,
        'sole_intervention': 'Global group execution order only: original M,C,E,W versus M,E,W,C',
        'unchanged': 'JOB_ALIGNED;all4 roles/group sizes;QGS50 and Q parameters;FA families/quotas;shared call cycle/pools;local order;G/L candidate order;PDDR;generation-end guide refresh',
        'observations': 'Same FeedbackAudit for all5; same composition provenance for all4 cooperative methods; metadata never enters pool selection',
        'fragment_provenance': 'Paid occurrence of retained pool record; duplicate offers do not refresh timestamp; fresh means same generation, not better quality',
        'partial_budgets': 'Capture actual eligible center opportunities/proposed/paid composition by generation; full shared generations have400 eligible opportunities; T may truncate different group phases',
        'fe_checkpoints': [15000], 'time_fractions': [.5, 1.],
        'metrics': {'primary_reference': [1.5]*3, 'sensitivity_references': [[1.25]*3, [2.]*3],
                    'igdplus_reference': 'Per-instance ND union of all5 methods x all5 seeds final deadline-valid fronts; approximate offline only',
                    'aggregation': 'Five seeds per instance, then six instances equally',
                    'practical_win': '>=1% instance mean and>=3/5 seed differences positive; symmetric losses; not statistical significance'},
        'interaction': '(HV_SHARE_LAST-HV_SYNC_LAST)-(HV_SHARE_ORIGINAL-HV_SYNC_ORIGINAL); raw per seed, instance mean normalized by mean SYNC_ORIGINAL',
        'hypothesis_signal': 'Predeclared descriptive signal: SHARE_LAST/SHARE_ORIGINAL meanT>=1%,>=3 practical instance wins,meanFE>0,and positive meanT interaction. Not a paper/scale-up gate; generic order improvements interpreted separately',
        'cost_boundary': 'T includes initialization/all search/repair/Q/local/sharing/archives/observers; JVM/input/config/offline QA/export in process/campaign wall separately',
        'continuation': 'Complete150 before quality interpretation unless correctness/resources/original45min cap; no other order enumeration,early refresh,round robin,new credit or tuning',
        'scope': 'Development timing-factor experiment only; no automatic further mechanism or formal step6'}


def jobs(protocol):
    rng = random.Random(202611025); result = []
    for row in protocol['instances']:
        for seed in protocol['algorithm_seeds']:
            labels = list(VARIANTS); rng.shuffle(labels)
            for label in labels:
                result.append({'phase': 'order', 'instance': row['stem'], 'seed': seed,
                               'variant': label, 'seconds': row['time_seconds']})
    if len(result) != protocol['runs']: raise ValueError('Complete6x5x5 matrix required')
    return result


def trial_folder(root, job): return root / 'trials' / job['phase'] / job['instance'] / str(job['seed']) / job['variant']

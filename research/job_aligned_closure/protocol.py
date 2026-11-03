"""Five locked methods, identical scientific inputs, and no outcome-driven branches."""
import copy
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / 'runs/semantic-repair-20261102-130342-703425'
VARIANTS = {
    'SO': {'mode': 'BASELINE', 'profile': 'SO'},
    'SO_JOB': {'mode': 'BASELINE_JOB_ALIGNED', 'profile': 'SO'},
    'SHARE': {'mode': 'SHARE', 'profile': 'SO'},
    'SHARE_JOB': {'mode': 'SHARE_JOB_ALIGNED', 'profile': 'SO'},
    'NSGA': {'mode': 'NSGA2_4V', 'profile': 'V2'},
}
PAIRS = (('SO_JOB', 'SO'), ('SHARE_JOB', 'SHARE'), ('SHARE', 'SO'),
         ('SHARE_JOB', 'SO_JOB'), ('SO', 'NSGA'), ('SHARE', 'NSGA'),
         ('SO_JOB', 'NSGA'), ('SHARE_JOB', 'NSGA'))


def make_protocol(previous):
    return {
        'version': 'job-aligned-closure-v1', 'purpose': 'Isolate the already-probed kernel in the full SO/SHARE loop',
        'instances': copy.deepcopy(previous['instances']),
        'algorithm_seeds': list(previous['algorithm_seeds']),
        'model': copy.deepcopy(previous['model']), 'variants': copy.deepcopy(VARIANTS),
        'runs': 150, 'phases': {'closure': list(VARIANTS)},
        'campaign_wall_cap_seconds': 5400, 'one_jvm_at_a_time': True,
        'planned_search_seconds': 1300, 'classic_setting': 0,
        'kernel_change': 'Only ordinary global proposals use the exact previous JOB_ALIGNED kernel; shared assemblies bypass it unchanged',
        'locked_search': 'population100,boundary15,QGS50,alpha1,gamma0.8,exploration0.8,randScale0.6,localCap30; original SO G+L200 PDDR; original four groups and family80+4x5; no parent retention',
        'locked_cooperation': 'Original fixed FA families, pools, compose frequency/caps, restore, validation and feedback; no change',
        'diagnostics': 'Same SemanticAudit for all five; previous MechanismCapture and standalone probes disabled',
        'metrics': {'primary_reference': [1.5] * 3, 'sensitivity_references': [[1.25] * 3, [2.] * 3],
                    'igdplus_reference': 'Per-instance ND union of all5 methods x all5 seeds final deadline-valid fronts, offline only',
                    'aggregation': 'Average seeds within each instance, then six instances equally',
                    'practical_win': 'instance mean effect>=1% and>=3/5 paired seeds positive; symmetric losses; not statistical significance',
                    'interaction': 'HV_SHARE_JOB-HV_SHARE-HV_SO_JOB+HV_SO, normalized by paired SO HV'},
        'fe_checkpoints': [15000], 'time_fractions': [.5, 1.],
        'censoring': 'Unreached FE remains censored; no lower FE threshold, extra run or imputation',
        'time_accounting': 'Search T includes initialization,QGS,kernel,repair,local search,sharing,archives,audit; JVM/input/assembly and offline replay/export measured in process/campaign wall separately',
        'seed_scope': 'Five previously registered development seeds, including the two not used in the immediately preceding 3-seed probe; no holdout claim',
        'continuation': 'Complete all150 unless implementation/resource failure or original wall cap; no tuning or automatic additional mechanism/scale-up',
        'scope': 'Bounded closed-loop development comparison; no original270 traffic light and no formal step6 verdict',
    }


def jobs(protocol):
    rng = random.Random(202611023)
    out = []
    for instance in protocol['instances']:
        for seed in protocol['algorithm_seeds']:
            labels = list(protocol['variants']); rng.shuffle(labels)
            for label in labels:
                out.append({'phase': 'closure', 'instance': instance['stem'], 'seed': seed,
                            'variant': label, 'seconds': instance['time_seconds']})
    if len(out) != protocol['runs']:
        raise ValueError('The complete 6x5x5 matrix is required')
    return out


def trial_folder(root, job):
    return root / 'trials' / job['phase'] / job['instance'] / str(job['seed']) / job['variant']

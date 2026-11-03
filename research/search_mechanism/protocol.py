"""Predeclared small development matrix; no parameter selection or paper-scale gate."""
from pathlib import Path
import copy
import random

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / 'runs/semantic-repair-20261102-130342-703425'
VARIANTS = {
    'SO': {'mode': 'BASELINE', 'profile': 'SO', 'parents': False},
    'SHARE': {'mode': 'SHARE', 'profile': 'SO', 'parents': False},
    'NSGA': {'mode': 'NSGA2_4V', 'profile': 'V2', 'parents': False},
    'SO_PARENT': {'mode': 'BASELINE', 'profile': 'SO', 'parents': True},
    'SHARE_PARENT': {'mode': 'SHARE', 'profile': 'SO', 'parents': True},
}


def make_protocol(previous):
    return {
        'version': 'search-mechanism-v1',
        'instances': copy.deepcopy(previous['instances']),
        'algorithm_seeds': previous['algorithm_seeds'][:3],
        'model': copy.deepcopy(previous['model']),
        'variants': copy.deepcopy(VARIANTS),
        'phases': {'capture': ['SO', 'SHARE', 'NSGA'], 'closure': ['SO_PARENT', 'SHARE_PARENT']},
        'initial_runs': 54, 'conditional_runs': 36, 'campaign_wall_cap_seconds': 5400,
        'one_jvm_at_a_time': True, 'classic_setting': 0,
        'primary_reference': [1.5] * 3, 'sensitivity_references': [[1.25] * 3, [2.] * 3],
        'kernel_names': ['PAPER', 'JOB_ALIGNED', 'CLASSIC_GLOBAL', 'CLASSIC_PERSONAL'],
        'kernel_replicates': 8,
        'kernel_case_anchors': {'early': 250, 'middle': 5000, 'late': 10000},
        'kernel_cases_per_anchor': 8,
        'kernel_phase_scope': 'Fixed global proposal counts, not equal relative search maturity; unreached anchors remain absent',
        'kernel_parent_sources': 'Each kernel sees the same frozen triple. NSGA triple=(parentA,parentA,parentB); CLASSIC_PERSONAL self-cross is auxiliary there',
        'kernel_main_comparison': 'CLASSIC_GLOBAL versus PAPER; JOB_ALIGNED is a single explicit representation variant; CLASSIC_PERSONAL auxiliary',
        'kernel_reference': 'Frozen generation-start parent population plus the three actual parent/teacher objective vectors; identical across kernels',
        'kernel_seed_policy': '910000000+trial_index*10000+case_index*100+rep; reset per candidate; same seed is not identical random draws',
        'kernel_constraints': 'Common parent fixed-FA family restored by job for all kernels, then common repair; family restore edits separate from final repair',
        'kernel_cost': 'Generation includes family restore and final repair; guarded evaluation includes shared archive overhead; rotated kernel execution order; startup/export/QA separate',
        'parent_replay_cost': 'All three parents per case receive charged replay and bit-exact objective checks; every probe child fully replayed offline',
        'capture': 'First2 and last completed generations plus partial-generation record; P/G/L/S and QGS steps1/10/25/50; no RNG and no additional search FE',
        'closure_gate': {'variants': ['SO', 'SHARE'], 'meanOracleParentGainPercentOfGL_at_least': 1., 'positive_instances_at_least': 4,
                         'aggregation': 'Generation mean per run, seed mean per instance, equal weight across six instances; either variant triggers both fixed closure variants'},
        'parent_variant': 'Keep original G then L and append P (300 records), same whole-pool PDDR, stable order and existing family quotas; no free evaluation',
        'fe_checkpoints': [15000], 'time_fractions': [.5, 1.],
        'scope': 'Two mechanism diagnostics on development cases; original v2/SO unchanged, no formal step6 or tuning',
    }


def jobs(protocol, phase):
    rng = random.Random(202611021 if phase == 'capture' else 202611022)
    out = []
    for row in protocol['instances']:
        for seed in protocol['algorithm_seeds']:
            labels = list(protocol['phases'][phase]); rng.shuffle(labels)
            for label in labels:
                out.append({'phase': phase, 'instance': row['stem'], 'seed': seed,
                            'variant': label, 'seconds': row['time_seconds']})
    return out

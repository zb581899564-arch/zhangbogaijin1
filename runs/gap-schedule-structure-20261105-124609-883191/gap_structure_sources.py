"""Authoritative paid checkpoint genomes; keep all declared budgets and seeds separate."""
import numpy as np

from run_long_budget_bridge import ROOT, read, rows

NAT = ROOT / 'runs/natural-regime-bench-20261105-073626-086353'
FRESH = ROOT / 'runs/conditional-exchange-20261105-121825-633105'


def cases():
    result = []
    for spec in read(NAT / 'protocol.json')['instances']:
        stem = spec['stem']
        for budget, kind, endpoint in (('FE', 'FE', 500000), ('TIME', 'TIME', spec['time_seconds'])):
            result.append({'spec': spec, 'seed': 12390003, 'stratum': 'NAT-' + budget, 'kind': kind, 'endpoint': endpoint,
                'left': NAT / stem / f'{budget}-FULL_NAT', 'right': NAT / stem / f'{budget}-NSGA_NAT'})
        for seed in read(FRESH / 'protocol.json')['seeds']:
            for budget, kind, endpoint in (('FE', 'FE', 100000), ('TIME', 'TIME', spec['time_seconds'])):
                result.append({'spec': spec, 'seed': seed, 'stratum': 'FRESH-OFF-' + budget, 'kind': kind, 'endpoint': endpoint,
                    'left': FRESH / stem / f'{budget}-{seed}-FULL_OFF', 'right': FRESH / stem / f'{budget}-{seed}-NSGA_OFF'})
    return result


def checkpoint(case, side):
    folder = case[side];receipt, = rows(folder / 'run-receipt.jsonl')
    point, = [p for p in rows(folder / 'anytime.jsonl')
              if p['checkpointKind'] == case['kind'] and p['checkpoint'] == case['endpoint']]
    assert point['reached'] and receipt['error'] is None
    selected = [p for p in rows(folder / 'checkpoint-solutions.jsonl')
                if p['checkpointKind'] == case['kind'] and p['checkpoint'] == case['endpoint']]
    assert {tuple(g['objectives']) for g in selected} == {tuple(p) for p in point['front']}
    assert all(g['bornFE'] <= point['fe'] and g['bornSeconds'] <= point['elapsedSeconds'] for g in selected)
    if case['kind'] == 'TIME':assert all(g['bornSeconds'] <= case['endpoint'] for g in selected)
    # Stable objective order supplies deterministic ties, never sample by resulting structural distance.
    selected.sort(key=lambda g: (tuple(g['objectives']), g['bornFE'], tuple(g['JS']), tuple(g['FA']), tuple(g['MA']), tuple(g['WA'])))
    assert len(selected) == len({tuple(g['objectives']) for g in selected})
    return selected


def by_job(genome):
    n = len(genome['JS']);assert sorted(genome['JS']) == list(range(n))
    result = np.empty((n, 3), dtype=int)
    for position, job in enumerate(genome['JS']):result[job] = [genome[k][position] for k in ('FA', 'MA', 'WA')]
    return result

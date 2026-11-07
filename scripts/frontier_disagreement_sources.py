"""Keep long natural/replay FE/TIME and short task budgets in separate descriptive strata."""
import numpy as np

from run_long_budget_bridge import ROOT, read, rows

NATURAL = ROOT / 'runs/natural-regime-bench-20261105-073626-086353'
TASK = ROOT / 'runs/center-task-pilot-20261105-113130-670918'


def cases():
    protocol = read(NATURAL / 'protocol.json'); result = []
    for spec in protocol['instances']:
        for budget, kind, endpoint in (('FE', 'FE', 500000), ('TIME', 'TIME', spec['time_seconds'])):
            for regime in ('NAT', 'REPLAY'):
                base = NATURAL / spec['stem']
                result.append({'stratum': f'{regime}-{budget}', 'spec': spec, 'seed': protocol['seed'],
                    'left': base / f'{budget}-FULL_{regime}', 'right': base / f'{budget}-NSGA_{regime}',
                    'leftName': 'FULL', 'rightName': 'NSGA', 'kind': kind, 'endpoint': endpoint})
        for seed in read(TASK / 'protocol.json')['freshSeeds']:
            for left, right in (('OFF', 'NSGA'), ('FIXED', 'OFF'), ('FIXED', 'NSGA')):
                base = TASK / spec['stem']
                result.append({'stratum': f'TASK-{left}-{right}', 'spec': spec, 'seed': seed,
                    'left': base / f'{seed}-{left}', 'right': base / f'{seed}-{right}',
                    'leftName': left, 'rightName': right, 'kind': 'FE', 'endpoint': 13300})
    return result


def load(case, side):
    folder = case[side]; receipt, = rows(folder / 'run-receipt.jsonl')
    assert receipt['error'] is None and receipt['failed'] == receipt['timeInterruptedAttempts']
    point, = [p for p in rows(folder / 'anytime.jsonl')
              if p['checkpointKind'] == case['kind'] and p['checkpoint'] == case['endpoint']]
    assert point['reached'] and point['fe'] <= receipt['successful']
    norm = case['spec']['normalization']
    front = (np.asarray(point['front']) - norm['lower']) / norm['scale']
    assert front.ndim == 2 and front.shape[1] == 3 and len(front)
    return front, {'folder': str(folder), 'endpointKind': case['kind'], 'endpoint': case['endpoint'],
                   'actualPaidFEAtSnapshot': point['fe'], 'successfulFEInRun': receipt['successful']}

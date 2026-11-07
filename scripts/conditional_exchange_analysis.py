"""Prospective screening of the common sampler, no seed/window selection."""
import numpy as np

from run_long_budget_bridge import rows, write_once, hypervolume, igd_plus, nondominated
from conditional_exchange_design import ARMS, SEEDS, FE_LIMIT


def metrics(root, spec, budget):
    values = {}; fronts = {}; norm = spec['normalization']
    kind, endpoint = ('FE', FE_LIMIT) if budget == 'FE' else ('TIME', spec['time_seconds'])
    for seed in SEEDS:
        for arm in ARMS:
            folder = root / spec['stem'] / f'{budget}-{seed}-{arm}'
            point, = [p for p in rows(folder / 'anytime.jsonl') if p['checkpointKind'] == kind and p['checkpoint'] == endpoint]
            assert point['reached']
            fronts[seed, arm] = (np.asarray(point['front']) - norm['lower']) / norm['scale']
    reference = nondominated(np.vstack(list(fronts.values())))
    for key, front in fronts.items():
        values[key] = {'HV': {str(ref): float(hypervolume(front, (ref,) * 3)) for ref in (1.25, 1.5, 2.)},
                       'IGDplus': float(igd_plus(front, reference)), 'frontSize': len(front)}
    return values


def compare(values, left, right):
    pairs = []
    for seed in SEEDS:
        a, b = values[seed, left], values[seed, right]; den = a['IGDplus'] + b['IGDplus']
        pairs.append({'seed': seed, 'HVgainPct': {ref: 100 * (a['HV'][ref] / b['HV'][ref] - 1) for ref in a['HV']},
                      'IGDplusSymmetricWorseningPct': 200 * (a['IGDplus'] - b['IGDplus']) / den if den else 0.})
    return {'pairs': pairs, 'medianHVgainPct': {ref: float(np.median([p['HVgainPct'][ref] for p in pairs]))
                                              for ref in ('1.25', '1.5', '2.0')},
            'medianIGDplusSymmetricWorseningPct': float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs]))}


def analyze(root, specs):
    results = []
    for spec in specs.values():
        levels = []
        for budget in ('FE', 'TIME'):
            values = metrics(root, spec, budget)
            compared = {label: compare(values, left, right) for label, left, right in
                (('fullKernelEffect', 'FULL_ON', 'FULL_OFF'), ('nsgaKernelEffect', 'NSGA_ON', 'NSGA_OFF'),
                 ('newStrongComparison', 'FULL_ON', 'NSGA_ON'), ('originalStrongComparison', 'FULL_OFF', 'NSGA_OFF'))}
            own, classic = compared['fullKernelEffect'], compared['newStrongComparison']
            gates = {'ownBenefit': own['medianHVgainPct']['1.5'] >= (.5 if budget == 'TIME' else 0.) and
                        all(p['HVgainPct']['1.5'] >= -.5 for p in own['pairs']),
                     'strongClassic': classic['medianHVgainPct']['1.5'] >= -1 and
                        all(p['HVgainPct']['1.5'] >= -5 for p in classic['pairs']),
                     'referenceRobustness': all(own['medianHVgainPct'][ref] >= 0 and
                        classic['medianHVgainPct'][ref] >= -2 for ref in ('1.25', '2.0')),
                     'auxiliary': classic['medianIGDplusSymmetricWorseningPct'] <= 5}
            levels.append({'budget': budget, 'comparisons': compared, 'gates': gates, 'pass': all(gates.values()),
                'metrics': [{'seed': seed, 'arm': arm, **m} for (seed, arm), m in values.items()]})
            print('CONDITIONAL_EXCHANGE_ANALYZED', spec['stem'], budget, 'own', own['medianHVgainPct']['1.5'],
                  'newNSGA', classic['medianHVgainPct']['1.5'], 'gates', gates, flush=True)
        summary = {'stem': spec['stem'], 'levels': levels, 'pass': all(level['pass'] for level in levels)}
        write_once(root / spec['stem'] / 'analysis.json', summary); results.append(summary)
    passed = all(r['pass'] for r in results)
    result = {'instances': results, 'worthFullComparisonDesign': passed,
        'decision': 'FULL_500K_DUTY_SHARE_LI_PROTOCOL_ONLY' if passed else 'STOP_EXACT_CONDITIONAL_EXCHANGE_KERNEL',
        'goalAchieved': False, 'priorEmptyNeighborhoodStopUnchanged': True}
    write_once(root / 'analysis.json', result); return result

"""Predeclared screening uses complete algorithm endpoints, not the old conditional audit sums."""
import numpy as np

from run_long_budget_bridge import rows, write_once, hypervolume, igd_plus, nondominated
from program_exit_design import ARMS, SEEDS, FE_LIMIT


def metrics(root, spec, budget):
    kind, endpoint = ('FE', FE_LIMIT) if budget == 'FE' else ('TIME', spec['time_seconds'])
    fronts = {};norm = spec['normalization']
    for seed in SEEDS:
        for arm in ARMS:
            folder = root / spec['stem'] / f'{budget}-{seed}-{arm}'
            point, = [p for p in rows(folder / 'anytime.jsonl') if p['checkpointKind'] == kind and p['checkpoint'] == endpoint]
            assert point['reached']
            fronts[seed, arm] = (np.asarray(point['front']) - norm['lower']) / norm['scale']
    reference = nondominated(np.vstack(list(fronts.values())))
    return {key: {'HV': {str(ref): float(hypervolume(front, (ref,) * 3)) for ref in (1.25, 1.5, 2.)},
                  'IGDplus': float(igd_plus(front, reference))} for key, front in fronts.items()}


def compare(values, left, right):
    pairs = []
    for seed in SEEDS:
        a, b = values[seed, left], values[seed, right];denominator = a['IGDplus'] + b['IGDplus']
        pairs.append({'seed': seed, 'HVgainPct': {ref: 100 * (a['HV'][ref] / b['HV'][ref] - 1) for ref in a['HV']},
            'IGDplusSymmetricWorseningPct': 200 * (a['IGDplus'] - b['IGDplus']) / denominator if denominator else 0.})
    return {'pairs': pairs, 'medianHVgainPct': {ref: float(np.median([p['HVgainPct'][ref] for p in pairs]))
                                              for ref in ('1.25', '1.5', '2.0')},
        'medianIGDplusSymmetricWorseningPct': float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs]))}


def analyze_budget(root, specs, budget):
    results = []
    for spec in specs.values():
        values = metrics(root, spec, budget)
        compared = {label: compare(values, left, right) for label, left, right in (
            ('fullExitEffect', 'FULL_ON', 'FULL_OFF'), ('nsgaExitEffect', 'NSGA_ON', 'NSGA_OFF'),
            ('matchedStrongComparison', 'FULL_ON', 'NSGA_ON'), ('oldStrongComparison', 'FULL_OFF', 'NSGA_OFF'),
            ('againstUnchangedStrong', 'FULL_ON', 'NSGA_OFF'))}
        own, classic = compared['fullExitEffect'], compared['matchedStrongComparison']
        gates = {'ownBenefit': own['medianHVgainPct']['1.5'] >= (.5 if budget == 'TIME' else 0.) and
                    all(p['HVgainPct']['1.5'] >= -.5 for p in own['pairs']),
                 'strongClassic': classic['medianHVgainPct']['1.5'] >= -1 and
                    all(p['HVgainPct']['1.5'] >= -5 for p in classic['pairs']),
                 'referenceRobustness': all(own['medianHVgainPct'][ref] >= 0 and classic['medianHVgainPct'][ref] >= -2
                                           for ref in ('1.25', '2.0')),
                 'auxiliary': classic['medianIGDplusSymmetricWorseningPct'] <= 5}
        result = {'stem': spec['stem'], 'budget': budget, 'comparisons': compared, 'gates': gates,
            'pass': all(gates.values()), 'metrics': [{'seed': seed, 'arm': arm, **value} for (seed, arm), value in values.items()]}
        write_once(root / spec['stem'] / f'analysis-{budget}.json', result);results.append(result)
        print('PROGRAM_EXIT_ANALYSIS', spec['stem'], budget, 'ownMedian', own['medianHVgainPct']['1.5'],
              'matchedNsgaMedian', classic['medianHVgainPct']['1.5'], 'gates', gates, flush=True)
    result = {'budget': budget, 'instances': results, 'pass': all(r['pass'] for r in results), 'goalAchieved': False}
    write_once(root / f'analysis-{budget}.json', result)
    return result

"""Known-target two-factor effects, not performance of an implemented proposal policy."""
import numpy as np
from pathlib import Path

from run_long_budget_bridge import read, rows, write_once, hypervolume
from fa_admission_volume import volume
from frontier_disagreement_geometry import single_gain


def analyze(root, spec):
    folder = root / spec['stem'];selected = read(folder / 'selected-pairs.json')
    outcomes = {(r['case'], r['method']): r for r in rows(folder / 'probe/outcomes.jsonl')}
    result = [];source_cache = {};norm = spec['normalization']
    for chosen in selected:
        if chosen['targetIndex'] is None:result.append({**chosen, 'matched': False});continue
        path = chosen['source']
        if path not in source_cache:
            source = read(Path(path));front = (np.asarray([p['objectives'] for p in source['parentGenomes']]) - norm['lower']) / norm['scale']
            source_cache[path] = front
        front = source_cache[path];gains = {}
        for method in ('PARENT', 'ORDER_ONLY', 'BUNDLE_ONLY', 'TARGET'):
            row = outcomes[chosen['case'], method];point = (np.asarray(row['genome']['objectives']) - norm['lower']) / norm['scale']
            gain = single_gain(front, point)
            direct = volume(np.vstack([front, point])) - volume(front);assert abs(gain - direct) < 1e-11
            gains[method] = gain
        assert gains['PARENT'] < 1e-11
        result.append({**chosen, 'matched': True, 'singleHVgain': gains,
            'twoFactorHVInteraction': gains['TARGET'] - gains['ORDER_ONLY'] - gains['BUNDLE_ONLY'],
            'orderAtLeastHalfTarget': gains['ORDER_ONLY'] >= .5 * gains['TARGET'] if gains['TARGET'] > 1e-10 else None,
            'bundleAtLeastHalfTarget': gains['BUNDLE_ONLY'] >= .5 * gains['TARGET'] if gains['TARGET'] > 1e-10 else None,
            'bothBelowTenthTarget': max(gains['ORDER_ONLY'], gains['BUNDLE_ONLY']) < .1 * gains['TARGET'] if gains['TARGET'] > 1e-10 else None})
    strata = []
    keys = sorted({(p['seed'], p['stratum']) for p in selected})
    for seed, stratum in keys:
        cases = [p for p in result if p['seed'] == seed and p['stratum'] == stratum]
        matched = [p for p in cases if p['matched']];sums = {method: sum(p['singleHVgain'][method] for p in matched)
                 for method in ('PARENT', 'ORDER_ONLY', 'BUNDLE_ONLY', 'TARGET')}
        summary = {'seed': seed, 'stratum': stratum, 'plannedPairs': len(cases), 'matchedPairs': len(matched),
            'positiveTargetPairs': sum(p['singleHVgain']['TARGET'] > 1e-10 for p in matched),
            'sumSingleHVgains': sums, 'orderSumRatioToTarget': sums['ORDER_ONLY'] / sums['TARGET'] if sums['TARGET'] > 1e-12 else None,
            'bundleSumRatioToTarget': sums['BUNDLE_ONLY'] / sums['TARGET'] if sums['TARGET'] > 1e-12 else None,
            'bothBelowTenthTargetPairs': sum(p['bothBelowTenthTarget'] is True for p in matched)}
        strata.append(summary);print('SCHEDULE_FACTOR_STRATUM', spec['stem'], summary, flush=True)
    write_once(folder / 'analysis.json', {'stem': spec['stem'], 'strata': strata, 'pairs': result,
        'scope': 'Privileged target schedule-factor counterfactual only; not algorithm value or fatigue-specific proof.'})
    return {'stem': spec['stem'], 'strata': strata}

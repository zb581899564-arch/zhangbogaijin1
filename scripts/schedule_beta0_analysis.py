"""Compare identical four corners on a shared parent-singleton scoring definition in both physical models."""
from collections import defaultdict
import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume


def four_gains(points, normalization):
    front = {k: (np.asarray(v) - normalization['lower']) / normalization['scale'] for k, v in points.items()}
    parent = front['PARENT'];base = hypervolume([parent], (1.5,) * 3)
    gains = {k: max(0., float(hypervolume([parent, value], (1.5,) * 3) - base)) for k, value in front.items()}
    informative = gains['TARGET'] > 1e-10
    ratio = max(gains['ORDER_ONLY'], gains['BUNDLE_ONLY']) / gains['TARGET'] if informative else None
    p, t = np.asarray(points['PARENT']), np.asarray(points['TARGET'])
    return {'singleHVgainAgainstParent': gains, 'targetStrictlyDominatesParent': bool(np.all(t <= p) and np.any(t < p)),
            'targetPositiveHVgain': informative, 'bestSingleFactorRecoveryRatio': ratio,
            'bothSingleFactorsBelowTenthTarget': ratio < .1 if informative else None,
            'twoFactorInteraction': gains['TARGET'] - gains['ORDER_ONLY'] - gains['BUNDLE_ONLY']}


def analyze(root, dynamic, spec):
    stem = spec['stem'];selected = read(dynamic / stem / 'selected-pairs.json')
    old = {(r['case'], r['method']): r['genome'] for r in rows(dynamic / stem / 'probe/outcomes.jsonl')}
    new = {(r['case'], r['method']): r['genome'] for r in rows(root / stem / 'probe/outcomes.jsonl')}
    assert old.keys() == new.keys();result = [];groups = defaultdict(list)
    for item in selected:
        if item['targetIndex'] is None:result.append({**item, 'matched': False});continue
        case = item['case'];d, z = {}, {}
        for method in ('PARENT', 'ORDER_ONLY', 'BUNDLE_ONLY', 'TARGET'):
            assert all(old[case, method][v] == new[case, method][v] for v in ('JS', 'FA', 'MA', 'WA'))
            d[method] = old[case, method]['objectives'];z[method] = new[case, method]['objectives']
        a, b = four_gains(d, spec['normalization']), four_gains(z, spec['normalization'])
        assert a['targetStrictlyDominatesParent'], 'Dynamic selected target lost source dominance'
        pair = {**item, 'matched': True, 'dynamic': a, 'beta0': b,
            'amplificationOfJointDependence': b['bestSingleFactorRecoveryRatio'] - a['bestSingleFactorRecoveryRatio']
                if a['targetPositiveHVgain'] and b['targetPositiveHVgain'] else None}
        result.append(pair);groups[item['seed'], item['stratum']].append(pair)
    summary = []
    for (seed, stratum), pairs in sorted(groups.items()):
        both = [p for p in pairs if p['dynamic']['targetPositiveHVgain'] and p['beta0']['targetPositiveHVgain']]
        amplification = [p['amplificationOfJointDependence'] for p in both]
        record = {'seed': seed, 'stratum': stratum, 'matchedPairs': len(pairs),
            'beta0TargetStrictDominators': sum(p['beta0']['targetStrictlyDominatesParent'] for p in pairs),
            'beta0TargetNoPositiveHV': sum(not p['beta0']['targetPositiveHVgain'] for p in pairs),
            'dynamicJointDependent': sum(p['dynamic']['bothSingleFactorsBelowTenthTarget'] is True for p in pairs),
            'beta0JointDependent': sum(p['beta0']['bothSingleFactorsBelowTenthTarget'] is True for p in pairs),
            'bothPositiveComparablePairs': len(both),
            'dynamicOnlyJointDependentAmongComparable': sum(p['dynamic']['bothSingleFactorsBelowTenthTarget'] is True and
                p['beta0']['bothSingleFactorsBelowTenthTarget'] is False for p in both),
            'beta0OnlyJointDependentAmongComparable': sum(p['beta0']['bothSingleFactorsBelowTenthTarget'] is True and
                p['dynamic']['bothSingleFactorsBelowTenthTarget'] is False for p in both),
            'medianAmplificationOfJointDependence': float(np.median(amplification)) if amplification else None}
        summary.append(record);print('SCHEDULE_BETA0_STRATUM', stem, record, flush=True)
    write_once(root / stem / 'analysis.json', {'stem': stem, 'strata': summary, 'pairs': result,
        'scope': 'Same genes and parent-singleton score in both models; targets selected under dynamic model, no beta0 optimization.'})
    return {'stem': stem, 'strata': summary}

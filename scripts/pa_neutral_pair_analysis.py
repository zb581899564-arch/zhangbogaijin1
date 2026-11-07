"""Paired donor rollback with identical receiver/mask/prior archive, reporting all three indicators."""
import numpy as np

from run_long_budget_bridge import rows, write_once, nondominated, hypervolume, igd_plus
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage


def analyze(folder, cases, normalization):
    records = rows(folder/'PAIRS/candidates.jsonl')
    index = {(r['case'], r['branch']): r for r in records}; assert len(index) == len(records) == 2*len(cases)
    normalize = lambda x: (np.asarray(x, float).reshape(-1, 3)-normalization['lower'])/normalization['scale']
    results = []
    for case in cases:
        actual, rollback = [index[case['case'], arm]['objectives'] for arm in ('ACTUAL', 'ROLLBACK')]
        assert actual == case['actualChild']['objectives']
        base = np.asarray(case['priorArchive'], float).reshape(-1, 3)
        a, b = nondominated(np.vstack([base, actual])), nondominated(np.vstack([base, rollback]))
        reference = nondominated(normalize(np.vstack([a, b])))
        ia, ib = igd_plus(normalize(a), reference), igd_plus(normalize(b), reference)
        hv = {}
        for r in (1.25, 1.5, 2.):
            hb = hypervolume(normalize(base), (r,)*3); assert hb > 1e-12
            ha, hr = hypervolume(normalize(a), (r,)*3), hypervolume(normalize(b), (r,)*3)
            hv[str(r)] = {'base': hb, 'actual': ha, 'rollback': hr, 'differencePctOfPriorHV': 100*(ha-hr)/hb}
        coverage = bidirectional_coverage(a, b)
        results.append({'case': case['case'], 'sourceBridgeFE': case['sourceBridge']['paidFE'], 'sourceRole': case['sourceBridge']['role'],
            'receiverFE': case['paidFE'], 'actualObjectives': actual, 'rollbackObjectives': rollback,
            'HV': hv, 'IGDplusActual': ia, 'IGDplusRollback': ib, 'IGDplusSymmetricWorseningPct': 200*(ia-ib)/(ia+ib) if ia+ib else 0.,
            'coverage': coverage, 'actualAcceptedInFrozenTrace': case['actualAccepted']})
    delta = [r['HV']['1.5']['differencePctOfPriorHV'] for r in results]
    igd = [r['IGDplusSymmetricWorseningPct'] for r in results]
    cd = [r['coverage']['C_A_B']-r['coverage']['C_B_A'] for r in results]
    useful = [r for r in results if r['HV']['1.5']['differencePctOfPriorHV'] > 1e-10
              and r['IGDplusSymmetricWorseningPct'] <= 1e-10 and r['coverage']['C_A_B']-r['coverage']['C_B_A'] >= -1e-10]
    checks = {'atLeast8Pairs': len(results) >= 8, 'atLeast3JointFavorablePairs': len(useful) >= 3,
        'atLeastOnePractical01pct': max(delta, default=0) >= .1,
        'positiveHVCountExceedsNegativeBy2': sum(x > 1e-10 for x in delta) >= sum(x < -1e-10 for x in delta)+2,
        'sumHVPositive': sum(delta) > 1e-10, 'medianIGDNonworse': bool(np.median(igd) <= 1e-10),
        'medianCoverageNonworse': bool(np.median(cd) >= -1e-10),
        'referenceSumDirectionStable': all(sum(r['HV'][str(ref)]['differencePctOfPriorHV'] for r in results) >= -1e-10 for ref in (1.25, 2.))}
    result = {'pairs': results, 'pairCount': len(results), 'positiveHVPairs': sum(x > 1e-10 for x in delta),
        'negativeHVPairs': sum(x < -1e-10 for x in delta), 'zeroHVPairs': sum(abs(x) <= 1e-10 for x in delta),
        'jointFavorablePairs': len(useful), 'practical01pctPairs': sum(x >= .1 for x in delta),
        'sumHVdifferencePctOfPriorHV': sum(delta), 'medianIGDplusSymmetricWorseningPct': float(np.median(igd)),
        'medianC_A_B': float(np.median([r['coverage']['C_A_B'] for r in results])),
        'medianC_B_A': float(np.median([r['coverage']['C_B_A'] for r in results])),
        'checks': checks, 'mechanismCluePass': all(checks.values()), 'fullAlgorithmPerformanceProved': False}
    write_once(folder/'pair-analysis.json', result); return result

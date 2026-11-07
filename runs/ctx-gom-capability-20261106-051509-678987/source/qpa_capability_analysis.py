"""Three-indicator complete-method comparisons, all controls and seeds; no search feedback."""
import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume, igd_plus, nondominated
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage


def endpoint(folder, phase, value):
    kind = 'TIME' if phase == 'TIME' else 'FE'
    point, = [p for p in rows(folder/'anytime.jsonl') if p['checkpointKind'] == kind and p['checkpoint'] == value and p['reached']]
    return point


def compare(a, b, seeds, values, fronts):
    pairs = []
    for seed in seeds:
        av, bv = values[seed, a], values[seed, b]; den = av['IGDplus']+bv['IGDplus']
        pairs.append({'seed': seed, 'HVEffectPct': {r: 100*(av['HV'][r]/bv['HV'][r] - 1) for r in av['HV']},
                      'IGDplusSymmetricWorseningPct': 200*(av['IGDplus'] - bv['IGDplus'])/den if den else 0.,
                      'coverage': bidirectional_coverage(fronts[seed, a], fronts[seed, b])})
    hv = {str(r): float(np.median([p['HVEffectPct'][str(r)] for p in pairs])) for r in (1.25, 1.5, 2.)}
    igd = float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs]))
    cd = [p['coverage']['C_A_B'] - p['coverage']['C_B_A'] for p in pairs]
    checks = {'medianHVAtLeast1pct': hv['1.5'] >= 1., 'referenceDirectionStable': all(hv[str(r)] >= 0 for r in (1.25, 2.)),
              'medianIGDNonworse': igd <= 0, 'medianCoverageNonworse': float(np.median(cd)) >= 0,
              'perSeedHVFloor': all(p['HVEffectPct']['1.5'] >= -1 for p in pairs),
              'perSeedIGDFloor': all(p['IGDplusSymmetricWorseningPct'] <= 5 for p in pairs),
              'perSeedCoverageFloor': min(cd) >= -.02}
    return {'A': a, 'B': b, 'pairs': pairs, 'medianHVEffectPct': hv, 'medianIGDplusSymmetricWorseningPct': igd,
            'medianC_A_B': float(np.median([p['coverage']['C_A_B'] for p in pairs])),
            'medianC_B_A': float(np.median([p['coverage']['C_B_A'] for p in pairs])),
            'checks': checks, 'jointPass': all(checks.values())}


def analyze(root, plan, phase):
    results = []
    for spec in plan['instances']:
        stem, norm = spec['stem'], spec['normalization']; value = spec['time_seconds'] if phase == 'TIME' else 500000
        folders = {(seed, arm): root/stem/str(seed)/(phase+'-'+arm) for seed in plan['seeds'] for arm in plan['arms']}
        fronts = {key: np.asarray(endpoint(folder, phase, value)['front'], float) for key, folder in folders.items()}
        normalized = {key: (front-norm['lower'])/norm['scale'] for key, front in fronts.items()}
        reference = nondominated(np.vstack(list(normalized.values())))
        values = {}
        for key, front in normalized.items():
            receipt, = rows(folders[key]/'run-receipt.jsonl')
            values[key] = {'seed': key[0], 'arm': key[1], 'frontSize': len(front),
                           'HV': {str(r): hypervolume(front, (r,)*3) for r in (1.25, 1.5, 2.)}, 'IGDplus': igd_plus(front, reference),
                           'objectiveMin': fronts[key].min(axis=0).tolist(), 'successfulFE': receipt['successful'],
                           'searchSeconds': receipt['searchSeconds'], 'stageFE': receipt['search']}
        comparisons = [compare('QPA_DIRECT', b, plan['seeds'], values, fronts) for b in plan['arms'][1:]]
        equal = compare('PA_EQUAL', 'PA_JOINT', plan['seeds'], values, fronts)
        results.append({'stem': stem, 'referenceSize': len(reference), 'observations': list(values.values()),
                        'comparisons': comparisons, 'equalityOnlyDiagnostic': equal,
                        'pass': all(r['jointPass'] for r in comparisons)})
    result = {'phase': phase, 'instances': results, 'pass': all(r['pass'] for r in results),
              'scope': 'Ordinary complete base qualification only; not a new four-role/shared contribution', 'goalAchieved': False}
    write_once(root/(phase.lower()+'-analysis.json'), result); return result

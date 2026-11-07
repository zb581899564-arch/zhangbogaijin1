"""Frozen primary endpoint and matched controls; no outcome-dependent endpoint selection."""
import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume, igd_plus, nondominated
from center_task_design import STEMS, SEEDS, ARMS, PRIMARY, LIMIT
from natural_local_support import ledger_rows


def folder(root, stem, seed, arm): return root / stem / f'{seed}-{arm}'


def common_inputs(root, stem):
    for seed in SEEDS:
        paths = [folder(root, stem, seed, arm) for arm in ARMS]
        initial = [(p / 'initial-population.jsonl').read_bytes() for p in paths]
        assert all(value == initial[0] for value in initial) and len(rows(paths[0] / 'initial-population.jsonl')) == 100
        expected = ledger_rows(root / stem / f'ledger-{seed}.csv')
        keys = ('visit', 'group', 'round', 'factory', 'paid')
        for p in paths:
            actual = ledger_rows(p / 'local-ledger.csv')
            assert [[r[k] for k in keys] for r in actual] == [[r[k] for k in keys] for r in expected]
            receipt, = rows(p / 'run-receipt.jsonl')
            for stage, count in {'initialization': 100, 'global': 10001, 'inter': 400, 'intra': 2800}.items():
                assert receipt['search'][stage + '.evaluations'] == count


def load(root, spec):
    data = {}; scale = np.asarray(spec['normalization']['scale'])
    lower = np.asarray(spec['normalization']['lower'])
    for seed in SEEDS:
        for arm in ARMS:
            path = folder(root, spec['stem'], seed, arm)
            receipt, = rows(path / 'run-receipt.jsonl')
            points = {int(r['checkpoint']): r for r in rows(path / 'anytime.jsonl')
                      if r['checkpointKind'] == 'FE' and r['reached']}
            assert PRIMARY in points and LIMIT in points
            fronts = {fe: (np.asarray(row['front']) - lower) / scale for fe, row in points.items()}
            data[seed, arm] = {'receipt': receipt, 'fronts': fronts}
    return data


def median(values): return float(np.median(values))


def effect(candidate, baseline): return 100 * (candidate / baseline - 1)


def symmetric_worse(candidate, baseline):
    return 200 * (candidate - baseline) / (candidate + baseline) if candidate + baseline else 0.0


def instance(root, spec):
    stem = spec['stem']; common_inputs(root, stem); data = load(root, spec)
    reference = nondominated(np.concatenate([v['fronts'][PRIMARY] for v in data.values()]))
    values = {}; records = []
    for (seed, arm), value in data.items():
        front = value['fronts'][PRIMARY]
        item = {'seed': seed, 'arm': arm, 'primaryFE': PRIMARY,
                'HV': {str(ref): float(hypervolume(front, (ref,) * 3)) for ref in (1.25, 1.5, 2.0)},
                'IGDplus': float(igd_plus(front, reference)), 'frontSize': len(front),
                'extremesNormalized': front.min(axis=0).tolist(), 'searchSeconds': value['receipt']['searchSeconds'],
                'stageHV1.5': {str(fe): float(hypervolume(f, (1.5,) * 3)) for fe, f in value['fronts'].items()}}
        records.append(item); values[seed, arm] = item
    comparisons = {}
    for arm in ARMS:
        if arm == 'FIXED': continue
        per_seed = []
        for seed in SEEDS:
            fixed, base = values[seed, 'FIXED'], values[seed, arm]
            per_seed.append({'seed': seed, 'HVgainPct': {ref: effect(fixed['HV'][ref], base['HV'][ref])
                                                       for ref in fixed['HV']},
                'IGDplusSymmetricWorseningPct': symmetric_worse(fixed['IGDplus'], base['IGDplus']),
                'searchCostRatio': fixed['searchSeconds'] / base['searchSeconds']})
        comparisons[arm] = {'pairs': per_seed,
            'medianHVgainPct': {ref: median([p['HVgainPct'][ref] for p in per_seed]) for ref in ('1.25', '1.5', '2.0')},
            'medianIGDplusSymmetricWorseningPct': median([p['IGDplusSymmetricWorseningPct'] for p in per_seed]),
            'medianSearchCostRatio': median([p['searchCostRatio'] for p in per_seed])}
    gates = {
        'originalGain': comparisons['OFF']['medianHVgainPct']['1.5'] >= 1 and
                        all(p['HVgainPct']['1.5'] >= 0 for p in comparisons['OFF']['pairs']),
        'beyondOwnershipAndTargets': all(comparisons[a]['medianHVgainPct']['1.5'] >= .5
                                        for a in ('OWNER_PDDR', 'EQUAL', 'PERMUTE')),
        'matchedClassic': comparisons['NSGA']['medianHVgainPct']['1.5'] >= 0,
        'referenceRobustness': all(comparisons[a]['medianHVgainPct'][ref] >= 0
                                   for a in ('OFF', 'NSGA') for ref in ('1.25', '2.0')),
        'igdAndTail': comparisons['NSGA']['medianIGDplusSymmetricWorseningPct'] <= 5 and
                      all(p['HVgainPct']['1.5'] >= -10 for p in comparisons['NSGA']['pairs']),
        'necessaryCost': all(comparisons[a]['medianSearchCostRatio'] <= 1.25 for a in ('OFF', 'NSGA'))}
    write_once(root / stem / 'analysis.json', {'stem': stem, 'primaryFE': PRIMARY,
        'empiricalReferenceFronts': len(data), 'empiricalReferenceSize': len(reference),
        'records': records, 'comparisons': comparisons, 'gates': gates, 'pass': all(gates.values()),
        'costLimits': 'Measured FE-run cost includes observer/paid digest; not a true TIME_LIMIT comparison.'})
    return {'stem': stem, 'gates': gates, 'pass': all(gates.values()),
            'medianHVgainPct': {a: c['medianHVgainPct']['1.5'] for a, c in comparisons.items()},
            'medianSearchCostRatio': {a: c['medianSearchCostRatio'] for a, c in comparisons.items()}}


def analyze(root, specs):
    results = [instance(root, specs[stem]) for stem in STEMS]
    passed = all(result['pass'] for result in results)
    result = {'instances': results, 'worthFullRegimeDesign': passed,
              'decision': 'FULL_REGIME_PROTOCOL_ONLY' if passed else 'STOP_FIXED_GENERATION_TASK_ARCHITECTURE',
              'goalAchieved': False, 'noWeightIdealOwnershipLedgerOrSeedRescue': True}
    write_once(root / 'analysis.json', result); return result

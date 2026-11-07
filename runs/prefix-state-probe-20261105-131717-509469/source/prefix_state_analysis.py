"""Score one offspring at a time against its original paid archive, without search feedback."""
from collections import defaultdict

import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume
from fa_admission_volume import volume
from prefix_state_design import METHODS, ROLES

CHILDREN = METHODS[2:]
TOLERANCE = 1e-12


def expected_encodings(folder):
    result = {}
    for line in (folder / 'cases.tsv').read_text('utf-8').splitlines():
        fields = line.split('\t')
        result[fields[0], fields[1]] = {name: list(map(int, fields[i + 3].split(',')))
                                      for i, name in enumerate(('JS', 'FA', 'MA', 'WA'))}
    return result


def normalized(value, scale):
    return (np.asarray(value, dtype=float) - scale['lower']) / scale['scale']


def score(cases, values, backgrounds, scale, reference):
    ref = (reference,) * 3
    archive = {seed: normalized(front, scale) for seed, front in backgrounds.items()}
    bases = {seed: volume(front, ref) for seed, front in archive.items()}
    result = []
    for case in cases:
        key = case['case'];seed = str(case['seed']);points = {
            method: normalized(values[key, method]['objectives'], scale) for method in METHODS}
        gains = {method: max(0., volume(np.vstack([archive[seed], point]), ref) - bases[seed])
                 for method, point in points.items()}
        assert gains['PARENT'] < TOLERANCE and gains['TEACHER'] < TOLERANCE, 'Previously paid source gained new archiveHV'
        own = hypervolume([points['PARENT']], ref)
        parent_gains = {method: max(0., hypervolume([points['PARENT'], points[method]], ref) - own)
                        for method in CHILDREN}
        result.append({'case': key, 'seed': case['seed'], 'receiverRank': case['receiverRank'],
            'role': case['role'], 'eligible': case['reason'] == 'ELIGIBLE',
            'archiveHV': bases[seed], 'archiveSingleGain': {m: gains[m] for m in CHILDREN},
            'parentSingleGain': parent_gains})
    return result


def beta_parent_scores(cases, values, scale):
    result = []
    for case in cases:
        points = {m: normalized(values[case['case'], m]['objectives'], scale) for m in METHODS}
        base = hypervolume([points['PARENT']], (1.5,) * 3)
        result.append({'case': case['case'], 'seed': case['seed'], 'role': case['role'],
            'parentSingleGain': {m: max(0., hypervolume([points['PARENT'], points[m]], (1.5,) * 3) - base)
                                 for m in CHILDREN}})
    return result


def summarize(records):
    means = {method: float(np.mean([r['archiveSingleGain'][method] for r in records])) for method in CHILDREN}
    differences = [r['archiveSingleGain']['PREFIX'] - max(r['archiveSingleGain'][m] for m in CHILDREN[1:])
                   for r in records]
    material = {(r['seed'], r['receiverRank']) for r in records
                if r['archiveSingleGain']['PREFIX'] >= .001 * r['archiveHV'] and r['archiveSingleGain']['PREFIX'] > TOLERANCE}
    receivers = {(r['seed'], r['receiverRank']) for r in records}
    return {'meanArchiveSingleGain': means,
        'winsVsBestMatchedControl': sum(d > TOLERANCE for d in differences),
        'lossesVsBestMatchedControl': sum(d < -TOLERANCE for d in differences),
        'tiesVsBestMatchedControl': sum(abs(d) <= TOLERANCE for d in differences),
        'materialReceivers': len(material), 'preselectedReceivers': len(receivers),
        'meanParentSingleGain': {m: float(np.mean([r['parentSingleGain'][m] for r in records])) for m in CHILDREN}}


def role_comparison(records):
    by_receiver = defaultdict(lambda: defaultdict(list))
    for r in records: by_receiver[r['seed'], r['receiverRank']][r['role']].append(r['archiveSingleGain']['PREFIX'])
    contrasts = []
    for (seed, rank), groups in sorted(by_receiver.items()):
        assert set(groups) == set(ROLES) and all(len(values) == 8 for values in groups.values())
        means = {role: float(np.mean(points)) for role, points in groups.items()}
        cross = float(np.mean([means[r] for r in ROLES if r != 'CENTER']))
        contrasts.append({'seed': seed, 'receiverRank': rank, 'roleMeanSingleGain': means,
                          'equalWeightSpecialistMean': cross, 'differenceVsCenter': cross - means['CENTER']})
    center = float(np.mean([r['roleMeanSingleGain']['CENTER'] for r in contrasts]))
    cross = float(np.mean([r['equalWeightSpecialistMean'] for r in contrasts]))
    wins = sum(r['differenceVsCenter'] > TOLERANCE for r in contrasts)
    losses = sum(r['differenceVsCenter'] < -TOLERANCE for r in contrasts)
    return {'centerMean': center, 'equalWeightSpecialistMean': cross, 'receiverWins': wins,
        'receiverLosses': losses, 'pass': cross > TOLERANCE and cross >= 1.05 * center and wins > losses,
        'receivers': contrasts}


def analyze(root, spec):
    folder = root / spec['stem'];cases = read(folder / 'cases.json');expected = expected_encodings(folder)
    models = {}
    for model in ('DYNAMIC', 'BETA0'):
        outcomes = rows(folder / model / 'probe/outcomes.jsonl')
        values = {(r['case'], r['method']): r['genome'] for r in outcomes}
        assert len(values) == len(outcomes) == len(expected) and values.keys() == expected.keys()
        for key, point in values.items(): assert all(point[k] == expected[key][k] for k in ('JS', 'FA', 'MA', 'WA'))
        checks = rows(folder / model / 'probe/prefix-state-checks.jsonl')
        assert len(checks) == len(cases)
        for case, check in zip(cases, checks):
            assert case['case'] == check['case'] and case['reason'] == check['reason']
            assert check['checkedFirstStageOperations'] == (len(case['block']) if case['reason'] == 'ELIGIBLE' else 0)
            assert check['eligible'] == check['exactPrefixTimeline'] == (case['reason'] == 'ELIGIBLE')
        models[model] = values
    scored = {ref: score(cases, models['DYNAMIC'], read(folder / 'backgrounds.json'), spec['normalization'], ref)
              for ref in (1.25, 1.5, 2.)}
    summaries = {str(ref): summarize(records) for ref, records in scored.items()}
    primary = summaries['1.5'];means = primary['meanArchiveSingleGain'];eligible = [c for c in cases if c['reason'] == 'ELIGIBLE']
    gates = {'eligibleCoverage': len(eligible) >= .25 * len(cases) and len({c['seed'] for c in eligible}) == 2,
        'materialReceiverCoverage': primary['materialReceivers'] >= .25 * primary['preselectedReceivers'],
        'meanQuality': means['PREFIX'] > TOLERANCE and means['PREFIX'] >= 1.05 * max(means[m] for m in CHILDREN[1:]),
        'pairedQuality': primary['winsVsBestMatchedControl'] > primary['lossesVsBestMatchedControl'],
        'referenceDirection': all(s['meanArchiveSingleGain']['PREFIX'] >
            max(s['meanArchiveSingleGain'][m] for m in CHILDREN[1:]) + TOLERANCE for s in summaries.values())}
    roles = role_comparison(scored[1.5])
    beta = beta_parent_scores(cases, models['BETA0'], spec['normalization'])
    result = {'stem': spec['stem'], 'coverage': read(folder / 'coverage.json'), 'referenceSummaries': summaries,
        'prefixGates': gates, 'worthIndependentPrefixContinuation': all(gates.values()), 'roleComparison': roles,
        'beta0MeanParentSingleGain': {m: float(np.mean([r['parentSingleGain'][m] for r in beta])) for m in CHILDREN},
        'goalAchieved': False}
    write_once(folder / 'analysis.json', {**result, 'dynamicPairs': scored[1.5], 'beta0Pairs': beta})
    print('PREFIX_STATE_ANALYSIS', result, flush=True)
    return result

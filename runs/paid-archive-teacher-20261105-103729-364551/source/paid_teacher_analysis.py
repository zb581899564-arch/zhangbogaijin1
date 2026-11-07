"""Exact fixed-background gains, paired recipients and independently checked source membership."""
from collections import Counter

import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume, nondominated
from research.composition_oracle.volume import UncoveredVolume
from paid_teacher_design import METHODS


def expected_pool(context, method):
    mask = {'PAID_ND': 8, 'HISTORY_ND': 7, 'CURRENT_ND': 2, 'INITIAL_ND': 1, 'RANDOM_KNOWN': 0}[method]
    eligible = [entry for entry in context['entries'] if not mask or entry['membership'] & mask]
    if method in ('PAID_ND', 'RANDOM_KNOWN'): return [entry['id'] for entry in eligible]
    objective_set = set(map(tuple, nondominated([e['point']['objectives'] for e in eligible])))
    used, chosen = set(), []
    for entry in eligible:
        point = tuple(entry['point']['objectives'])
        if point in objective_set and point not in used:
            chosen.append(entry['id']); used.add(point)
    return chosen


def relative(candidate, control):
    return 100 * (candidate / control - 1) if control > 1e-12 else None


def summarize(stem, cells, contexts_report, errors):
    means = {m: float(np.mean([c['methods'][m]['singleGain']['1.5'] for c in cells])) for m in METHODS}
    effects = {m: relative(means['PAID_ND'], means[m]) for m in METHODS if m != 'PAID_ND'}
    wins = {m: sum(c['methods']['PAID_ND']['singleGain']['1.5'] > c['methods'][m]['singleGain']['1.5'] + 1e-12
                   for c in cells) for m in ('HISTORY_ND', 'RANDOM_KNOWN')}
    informative = sum(c['informative'] for c in cells)
    strata = []
    for key in ('sourceSeed', 'step'):
        for value in sorted({c[key] for c in cells}):
            group = [c for c in cells if c[key] == value]
            strata.append({'key': key, 'value': value,
                           'means': {m: float(np.mean([c['methods'][m]['singleGain']['1.5'] for c in group])) for m in METHODS}})
    sensitivity = {ref: {m: float(np.mean([c['methods'][m]['singleGain'][ref] for c in cells])) for m in METHODS}
                   for ref in ('1.25', '2.0')}
    ratios = {m: float(np.median([c['methods']['PAID_ND']['necessaryCallSeconds'] /
                                  c['methods'][m]['necessaryCallSeconds'] for c in cells]))
              for m in ('HISTORY_ND', 'INITIAL_ND')}
    quality = informative >= 24 and all(effects[m] is not None and effects[m] >= threshold for m, threshold in
        (('HISTORY_ND', 10), ('INITIAL_ND', 10), ('CURRENT_ND', 5), ('RANDOM_KNOWN', 5)))
    coverage = all(value >= 27 for value in wins.values())
    robust = all((s['means']['PAID_ND'] > s['means'][m] if s['key'] == 'sourceSeed' else
                  s['means']['PAID_ND'] >= s['means'][m])
                 for s in strata for m in (('HISTORY_ND', 'RANDOM_KNOWN') if s['key'] == 'sourceSeed' else ('HISTORY_ND',)))
    reference = all(scores['PAID_ND'] > scores[m] for scores in sensitivity.values()
                    for m in ('HISTORY_ND', 'RANDOM_KNOWN'))
    cost = all(value <= 1.25 for value in ratios.values())
    result = {'stem': stem, 'recipientClusters': 48, 'informativeClusters': informative,
              'meanSingleAddedHV': means, 'candidateEffectsPct': effects, 'strictParentWins': wins,
              'strata': strata, 'referenceSensitivity': sensitivity, 'necessaryCallCostRatios': ratios,
              'qualityGate': bool(quality), 'coverageGate': bool(coverage), 'robustnessGate': bool(robust),
              'referenceGate': bool(reference), 'necessaryCostGate': bool(cost),
              'worthNativeClosedLoopDesign': bool(quality and coverage and robust and reference and cost),
              'maxIndependentHVError': max(errors), 'contexts': contexts_report, 'cases': cells,
              'limits': 'Conditional single-offspring same-candidate-count value only. Live archive API/maintenance, '
                        'complete sameFE/time, source duty uniqueness, fatigue specificity and independent confirmation unproven.'}
    return result


def analyze(root, spec):
    stem = spec['stem']; folder = root / stem
    contexts = read(folder / 'contexts.json')
    outcomes, pools = rows(folder / 'probe/outcomes.jsonl'), rows(folder / 'probe/pools.jsonl')
    paid_inputs = rows(folder / 'probe/paid-inputs.jsonl')
    receipts = rows(folder / 'probe/context-receipts.jsonl')
    assert len(outcomes) == 3840 and len(contexts) == len(receipts) == 6
    assert sum(r['successfulFE'] for r in receipts) == len(paid_inputs) + len(outcomes)
    normal = spec['normalization']; lower, scale = np.asarray(normal['lower']), np.asarray(normal['scale'])
    normalize = lambda values: (np.asarray(values, dtype=float).reshape(-1, 3) - lower) / scale
    cells, contexts_report, errors = [], [], []
    for context in contexts:
        id = context['id']; records = [r for r in outcomes if r['context'] == id]
        entries = {e['id']: e for e in context['entries']}
        current_inputs = [r for r in paid_inputs if r['context'] == id]
        receipt, = [r for r in receipts if r['context'] == id]
        assert receipt['status'] == 'COMPLETE' and receipt['failedFE'] == 0
        assert receipt['fullDecoderQA'] == receipt['successfulFE']
        assert receipt['successfulFE'] == len(context['entries']) + 640
        assert len(current_inputs) == len(entries)
        for record in current_inputs:
            assert record['genome'] == entries[record['id']]['point']
        ledger = sorted([r['paidFE'] for r in current_inputs] + [r['paidFE'] for r in records])
        assert ledger == list(range(1, receipt['successfulFE'] + 1))
        context_pools = [p for p in pools if p['context'] == id]
        for method in METHODS:
            actual = [p for p in context_pools if p['method'] == method]
            assert len(actual) == (1 if method == 'INITIAL_ND' else 16)
            expected = expected_pool(context, method)
            assert all(p['ids'] == expected for p in actual)
        pool_cost = {(p['rep'], p['method']): p['buildSeconds'] for p in context_pools}
        for record in records:
            pool = expected_pool(context, record['method'])
            assert record['guideId'] in pool
            receiver = context['recipients'][record['recipient']]
            assert record['parentId'] == receiver['parentId'] and record['personalId'] == receiver['personalId']
            assert record['guideFirstRole'] == entries[record['guideId']]['firstRole']
        scorers = {str(ref): UncoveredVolume(normalize(context['background']), (ref,) * 3)
                   for ref in (1.25, 1.5, 2.)}
        for scorer in scorers.values():
            assert max(scorer.gains(normalize([e['point']['objectives'] for e in context['entries']]))) < 1e-11
        gain = {ref: scorer.gains(normalize([r['child']['objectives'] for r in records]))
                for ref, scorer in scorers.items()}
        for index, record in enumerate(records):
            record['gains'] = {ref: float(values[index]) for ref, values in gain.items()}
        for recipient in range(8):
            metrics = {}
            for method in METHODS:
                selected = [r for r in records if r['recipient'] == recipient and r['method'] == method]
                assert {r['rep'] for r in selected} == set(range(16))
                fees = [pool_cost[(-1, method)] / 128 if method == 'INITIAL_ND'
                        else pool_cost[(r['rep'], method)] / 8 for r in selected]
                metrics[method] = {
                    'singleGain': {ref: float(np.mean([r['gains'][ref] for r in selected])) for ref in scorers},
                    'necessaryCallSeconds': float(np.mean([f + r['selectionSeconds'] + r['generationSeconds']
                                                          + r['evaluationSeconds'] for f, r in zip(fees, selected)])),
                    'guideFirstRoleCounts': dict(Counter(r['guideFirstRole'] for r in selected))}
            choices = [r for r in records if r['recipient'] == recipient]
            for rep in range(16):
                paired = [r for r in choices if r['rep'] == rep]
                assert len({r['selectSeed'] for r in paired}) == len({r['constructionSeed'] for r in paired}) == 1
            cells.append({'context': id, 'recipient': recipient, 'sourceSeed': context['sourceSeed'],
                          'step': context['step'], 'informative': any(r['gains']['1.5'] > 1e-10 for r in choices),
                          'methods': metrics})
        scorer = scorers['1.5']; background = normalize(context['background'])
        for record in (records[0], records[-1]):
            point = normalize([record['child']['objectives']])
            delta = hypervolume(np.vstack([background, point]), (1.5,) * 3) - scorer.background_hv
            error = abs(delta - float(scorer.gains(point)[0])); errors.append(error); assert error < 1e-11
        contexts_report.append({'id': id, 'seed': context['sourceSeed'], 'step': context['step'],
            'preBatchFE': context['preBatchFE'], 'commonInputFE': len(entries),
            'sourcePoolSizes': {m: len(expected_pool(context, m)) for m in METHODS},
            'commonReconstructionEvaluationSeconds': sum(r['reconstructionSeconds'] + r['evaluationSeconds']
                                                        for r in current_inputs),
            'offlineQASeconds': receipt['offlineQASeconds']})
    result = summarize(stem, cells, contexts_report, errors)
    write_once(folder / 'analysis.json', result)
    return result

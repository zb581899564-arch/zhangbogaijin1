"""Common-reference arm sets and raw paired differences; no best-of-RANDOM oracle."""
import csv
import numpy as np
from transfer_common import ARMS, write


def table(path, rows):
    with path.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def strict_better(a, b, tolerance=1e-8):
    a, b = np.asarray(a), np.asarray(b)
    return bool(np.all(a <= b) and np.any(b - a > tolerance))


def group_metrics(points, a0, reference, scale, seed):
    from analysis_metrics import metrics, pair
    scores = {arm: metrics([*a0, *points[arm]], reference, scale) for arm in ARMS}
    baseline = metrics(a0, reference, scale)
    return dict(metrics=scores, baseline=baseline,
                versusA0={arm: pair(seed, value, baseline) for arm, value in scores.items()},
                prunedComparisons={arm: pair(seed, scores['PRUNED'], scores[arm])
                                   for arm in ARMS if arm != 'PRUNED'})


def export_groups(output, groups):
    rows = []
    for group, values in groups.items():
        for arm, scored in values['metrics'].items():
            effect = values['versusA0'][arm]
            rows.append(dict(group=group, arm=arm, frontSize=scored['frontSize'],
                             HV=scored['HV']['1.5'], IGDplus=scored['IGDplus'], IGD=scored['IGD'],
                             HVgainAboveA0Pct=effect['HVEffectPct']['1.5']))
    table(output / 'arm-metrics.csv', rows)
    pairs = []
    for group, values in groups.items():
        for control, effect in values['prunedComparisons'].items():
            pairs.append(dict(group=group, candidate='PRUNED', control=control,
                HVEffectPct=effect['HVEffectPct']['1.5'],
                IGDplusSymmetricImprovementPct=effect['IGDplusSymmetricImprovementPct'],
                **effect['coverage'], CdeltaPercentagePoints=100 * effect['Cdelta']))
    table(output / 'paired-set-metrics.csv', pairs)
    write(output / 'group-metrics.json', groups)


def decision(blocks, groups, source_ids):
    counts = {source: sum(b['source'] == source and b['prunedStrictlyDominatesFull'] for b in blocks)
              for source in source_ids}
    structural = sum(n >= 2 for n in counts.values()) >= 2
    overall = groups['ALL']
    capacity = overall['versusA0']['PRUNED']['HVEffectPct']['1.5'] >= 0.1
    comparisons = overall['prunedComparisons']
    gains = {arm: value['HVAbsoluteDifference']['1.5'] > 1e-12 or value['IGDplusImprovement'] > 1e-12
             for arm, value in comparisons.items()}
    reverse = {arm: value['HVEffectPct']['1.5'] < -1 or
               value['IGDplusSymmetricImprovementPct'] < -5 or value['Cdelta'] < -0.10
               for arm, value in comparisons.items()}
    passed = structural and capacity and all(gains.values()) and not any(reverse.values())
    return dict(structuralCounts=counts, structuralGate=structural, capacityGate=capacity,
                gainVersusEachControl=gains, majorReverseVersusControl=reverse,
                eligibleForFurtherDiscussion=passed,
                status='LOCAL_TRANSFER_SIGNAL_ONLY' if passed else 'STOP_THIS_LITERAL_TRANSFER_VERSION',
                scope='No algorithm-performance or independent-seed claim; mainline and original sharing unchanged')

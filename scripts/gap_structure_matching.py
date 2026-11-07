"""Encoding distance to existing strict dominators, not a construction or search guidance mechanism."""
import numpy as np

from gap_structure_sources import by_job


def order_distance(parent, target):
    rank = {job: i for i, job in enumerate(target['JS'])};inversions = 0;possible = 0
    assignment = by_job(parent)[:, 0]
    for factory in sorted(set(assignment)):
        positions = [rank[job] for job in parent['JS'] if assignment[job] == factory]
        possible += len(positions) * (len(positions) - 1) // 2
        inversions += sum(positions[i] > positions[j] for i in range(len(positions)) for j in range(i + 1, len(positions)))
    return {'withinParentFactoriesInversions': inversions, 'possibleWithinFactoryPairs': possible,
            'withinFactoryInversionFraction': inversions / possible if possible else 0.}


def match(parent, targets, scale):
    objectives = np.asarray([p['objectives'] for p in targets]);base = np.asarray(parent['objectives'])
    eligible = np.flatnonzero(np.all(objectives <= base, axis=1) & np.any(objectives < base, axis=1))
    if not len(eligible):return None
    old = by_job(parent);candidates = np.asarray([by_job(targets[i]) for i in eligible])
    fa = np.count_nonzero(candidates[:, :, 0] != old[:, 0], axis=1)
    bundles = np.count_nonzero(np.any(candidates != old, axis=2), axis=1)
    objective_distance = np.sqrt(np.sum(((objectives[eligible] - base) / scale) ** 2, axis=1))
    chosen = min(range(len(eligible)), key=lambda j: (int(fa[j]), int(bundles[j]), float(objective_distance[j]), int(eligible[j])))
    index = int(eligible[chosen]);new = candidates[chosen]
    same_fa = old[:, 0] == new[:, 0]
    return {'targetIndex': index, 'strictDominators': len(eligible), 'minimumChangedFactoryJobs': int(fa.min()),
        'anyDominatorSameCompleteFA': bool(np.any(fa == 0)), 'selectedChangedBundleJobs': int(bundles[chosen]),
        'selectedSameFactoryChangedResourceJobs': int(np.count_nonzero(same_fa & np.any(old[:, 1:] != new[:, 1:], axis=1))),
        'selectedChangedFirstMachineJobs': int(np.count_nonzero(old[:, 1] != new[:, 1])),
        'selectedChangedFirstWorkerJobs': int(np.count_nonzero(old[:, 2] != new[:, 2])),
        'assignmentChangeFraction': int(fa.min()) / len(old), 'bundleChangeFraction': int(bundles[chosen]) / len(old),
        **order_distance(parent, targets[index])}


def fixtures():
    parent = {'JS': [0, 1, 2, 3], 'FA': [0, 1, 0, 1], 'MA': [0] * 4, 'WA': [0] * 4, 'objectives': [5., 5., 5.]}
    neutral = {'JS': [1, 0, 3, 2], 'FA': [1, 0, 1, 0], 'MA': [0] * 4, 'WA': [0] * 4, 'objectives': [4., 4., 4.]}
    result = match(parent, [neutral], np.ones(3))
    assert result['minimumChangedFactoryJobs'] == result['selectedChangedBundleJobs'] == 0
    assert result['withinParentFactoriesInversions'] == 0 and result['anyDominatorSameCompleteFA']
    assert match(parent, [parent], np.ones(3)) is None
    reversed_local = {**parent, 'JS': [2, 1, 0, 3]}
    assert order_distance(parent, reversed_local)['withinParentFactoriesInversions'] == 1
    return {'status': 'PASS', 'canonicalAssignmentIgnoresNeutralInterleaving': True,
            'strictDominanceNotEquality': True, 'knownWithinFactoryKendallDistance': True,
            'searchFE': 0, 'decoderCalls': 0}

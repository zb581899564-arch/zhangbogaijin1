"""Exact post-hoc objective geometry. No problem, decoder or candidate generation is imported."""
import numpy as np

from research.dynamic_benchmark.metrics import hypervolume, nondominated


def hv(front, axis=0, upper=1.5):
    reference = np.full(3, 1.5); reference[axis] = upper
    return float(hypervolume(front, reference))


def single_gain(front, point):
    """Uncovered part of the existing point's dominated box, clipped to the fixed HV reference."""
    if np.any(point >= 1.5) or np.any(np.all(front <= point, axis=1)): return 0.0
    box = float(np.prod(1.5 - point))
    covered = hv(np.maximum(front, point))
    value = box - covered
    assert value >= -1e-10
    return max(0.0, value)


def missing(front, other, total_missing):
    gains = np.asarray([single_gain(front, point) for point in other])
    best = int(np.argmax(gains)); point = other[best]
    # Directed additive epsilon and per-target shortfalls do not weight dense target regions by count.
    delta = front[None, :, :] - other[:, None, :]
    distance = np.maximum(delta, 0).max(axis=2)
    near = distance.argmin(axis=1); gaps = distance[np.arange(len(other)), near]
    worst = int(np.argmax(gaps))
    return {'bestSingleGain': float(gains[best]), 'bestSinglePoint': point.tolist(),
        'bestSingleShareOfMissingVolume': float(gains[best] / total_missing) if total_missing > 1e-10 else None,
        'allPointGainSumNotUnion': float(gains.sum()), 'positiveSinglePoints': int(np.count_nonzero(gains > 1e-10)),
        'weakPointCoverage': float(np.mean(np.any(np.all(front[None, :, :] <= other[:, None, :], axis=2), axis=1))),
        'additiveEpsilonPlus': float(gaps[worst]), 'worstTarget': other[worst].tolist(),
        'nearestToWorstTarget': front[near[worst]].tolist(),
        'shortfallAtWorstTarget': np.maximum(delta[worst, near[worst]], 0).tolist()}


def compare(left, right):
    joint = nondominated(np.vstack([left, right])); a, b, both = hv(left), hv(right), hv(joint)
    parts = []
    for axis in range(3):
        cuts = [0., *map(float, np.quantile(joint[:, axis], [.25, .5, .75])), 1.5]
        assert cuts == sorted(cuts)
        slabs = []
        for lo, hi in zip(cuts, cuts[1:]):
            av, bv, jv = [hv(front, axis, hi) - hv(front, axis, lo) for front in (left, right, joint)]
            slabs.append({'lower': lo, 'upper': hi, 'leftHV': av, 'rightHV': bv,
                          'leftMissingRightVolume': max(0., jv - av),
                          'rightMissingLeftVolume': max(0., jv - bv), 'signedRightMinusLeft': bv - av})
        assert abs(sum(p['signedRightMinusLeft'] for p in slabs) - (b - a)) < 1e-10
        assert abs(sum(p['leftMissingRightVolume'] for p in slabs) - (both - a)) < 1e-10
        parts.append({'axis': axis, 'slabs': slabs})
    return {'leftHV': a, 'rightHV': b, 'jointHV': both, 'leftVsRightHVPct': 100 * (a / b - 1),
        'leftMissingRightPctOfOwnHV': 100 * (both / a - 1),
        'rightMissingLeftPctOfOwnHV': 100 * (both / b - 1),
        'leftMissing': missing(left, right, both - a), 'rightMissing': missing(right, left, both - b),
        'axisPartitions': parts, 'leftMinimum': left.min(axis=0).tolist(),
        'rightMinimum': right.min(axis=0).tolist(), 'leftPoints': len(left), 'rightPoints': len(right)}


def arithmetic_fixtures():
    generator = np.random.default_rng(0x6513)
    for _ in range(12):
        front = nondominated(generator.uniform(.1, 1.6, (12, 3)))
        point = generator.uniform(.1, 1.6, 3)
        direct = hv(np.vstack([front, point])) - hv(front)
        assert abs(single_gain(front, point) - direct) < 1e-11
    front = np.asarray([[.5, .5, .5]])
    assert single_gain(front, np.asarray([.6, .6, .6])) == 0
    assert abs(single_gain(front, np.asarray([.25, .5, .5])) - .25) < 1e-12
    return {'status': 'PASS', 'randomBoxVsDirectHVChecks': 12, 'knownDominanceAndBoxFixtures': 2,
            'searchFE': 0, 'decoderCalls': 0}

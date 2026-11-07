"""Independent direct-state bytes, joint move and mean-linkage checks; no objective calls."""
import hashlib
import struct

import numpy as np

from qgomea_reference_math import inverse, position_mix, order_mix


def identity(point):
    n = len(point['resources'])
    data = struct.pack('>i', n) + struct.pack('>' + 'i'*n, *point['resources'])
    data += struct.pack('>' + 'i'*n, *point['positions']) + struct.pack('>ddd', *point['objectives'])
    return hashlib.sha256(data).hexdigest()


def vectors(point, catalog):
    order = inverse(point['positions'])
    return [order, *[[catalog[point['resources'][job]][k] for job in order] for k in range(3)]]


def paid_bytes(point, catalog, fe):
    result = struct.pack('>q', fe)
    for vector in vectors(point, catalog):
        result += struct.pack('>i', len(vector)) + struct.pack('>' + 'i'*len(vector), *vector)
    return result + struct.pack('>ddd', *point['objectives'])


def child(event, parent, donor, mask, catalog, factories):
    resources = parent['resources'].copy()
    for job in mask:
        resources[job] = donor['resources'][job]
    if event['phase'] == 1:
        assert event['reference'] in mask
        positions, _ = position_mix(parent['positions'], donor['positions'], mask, event['reference'])
    else:
        assert event['reference'] == -1
        positions = order_mix(parent['positions'], donor['positions'], mask)
    fallback = len({catalog[r][0] for r in resources}) != factories
    assert event['fallback'] == fallback
    if fallback:
        resources, positions = parent['resources'].copy(), parent['positions'].copy()
        assert event['objectives'] == parent['objectives']
    return dict(event, resources=resources, positions=positions)


def hierarchy(matrix, subsets):
    """Check each merge against original-matrix cluster means, independent of Java's queue."""
    n = len(matrix)
    assert len(subsets) == 2*n - 1 and subsets[:n] == [[i] for i in range(n)]
    clusters = {i: [i] for i in range(n)}
    sums = {(i, j): float(matrix[i, j]) for i in range(n) for j in range(i + 1, n)}
    worst = 0.
    for index, group in enumerate(subsets[n:], n):
        assert group == sorted(set(group))
        children = [k for k, values in clusters.items() if set(values).issubset(group)]
        assert len(children) == 2
        a, b = children
        assert sorted(clusters[a] + clusters[b]) == group
        scores = {pair: total/(len(clusters[pair[0]])*len(clusters[pair[1]])) for pair, total in sums.items()}
        chosen = scores[tuple(sorted((a, b)))]; deficit = max(scores.values()) - chosen
        assert abs(deficit) < 1e-12; worst = max(worst, abs(deficit))
        new = {tuple(sorted((k, index))): sums[tuple(sorted((a, k)))] + sums[tuple(sorted((b, k)))]
               for k in clusters if k not in (a, b)}
        sums = {pair: value for pair, value in sums.items() if a not in pair and b not in pair}
        sums.update(new); del clusters[a]; del clusters[b]; clusters[index] = group
    assert list(clusters.values()) == [list(range(n))]
    return worst


def model_check(event, states, population):
    assert [p['id'] for p in event['parents']] == population and len(population) == 100
    positions = np.array([states[i]['positions'] for i in population], dtype=np.int64)
    n = positions.shape[1]
    expected = 1 - np.abs(positions[:, :, None] - positions[:, None, :]).sum(axis=0)/(100*(n - 1))
    np.fill_diagonal(expected, 0.)
    error = float(np.abs(expected - np.array(event['affinity'])).max()); assert error < 1e-12
    deficit = hierarchy(expected, event['fullSubsets'])
    cutoff = round((n/12.0)*10.0)
    assert event['cutoff'] == cutoff
    assert event['activeSubsets'] == [g for g in event['fullSubsets'] if len(g) < cutoff]
    return {'componentPairs': n*(n - 1)//2, 'maximumAffinityError': error, 'maximumMeanMergeDeficit': deficit}

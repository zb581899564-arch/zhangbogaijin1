"""Independent mathematical fixtures; this module does not implement or run an optimizer."""
from itertools import product
import math

import numpy as np

from run_long_budget_bridge import read, write_once
from prefix_state_design import source_pool, physical_key
from gap_structure_sources import by_job


def predicate_cases():
    points = list(product((0., 1., 2.), repeat=3))
    for mask in range(8):
        for first in points:
            for second in points:
                for cx, cy in product((0., .5, 1.), repeat=2): yield mask, cx, cy, first, second
        for coordinate in range(3):
            for delta in (-2e-5, -1.1e-5, -1e-5, -9.99e-6, -1e-6, 0., 1e-6, 9.99e-6, 1e-5, 1.1e-5, 2e-5):
                first = [1., 2., 3.];second = first.copy();first[coordinate] += delta
                yield mask, 0., 0., tuple(first), tuple(second)


def expected_predicates(case, tolerance=1e-5):
    mask, cx, cy, first, second = case
    if cx > 0 or cy > 0:
        strict = cx < cy;weak = cx <= cy
    else:
        signs = [(b - a if mask & (1 << d) else a - b) if abs(a - b) >= tolerance else 0.
                 for d, (a, b) in enumerate(zip(first, second))]
        weak = all(s >= 0 for s in signs);strict = weak and any(s > 0 for s in signs)
    result = [int(strict), int(weak)]
    for d in range(3):
        if cx > 0 or cy > 0: better, equal = cx < cy, cx == cy
        else:
            better = first[d] < second[d] if mask & (1 << d) else first[d] > second[d]
            equal = first[d] == second[d]
        result += [int(better), int(equal)]
    return result


def predicate_input(root):
    path = root / 'predicate-cases.tsv'
    with path.open('x', encoding='ascii') as output:
        for index, (mask, cx, cy, first, second) in enumerate(predicate_cases()):
            output.write('\t'.join(map(str, (index, mask, cx, cy, *first, *second))) + '\n')
    return index + 1


def dependency_input(root):
    cases = [];rng = np.random.default_rng(13490003)
    for stem in ('20_8_5_1', '100_2_3_1'):
        for seed in (11730007, 11730037):
            _, groups, source = source_pool(stem, seed)
            points = [p for values in groups.values() for p in values];n = len(points[0]['JS'])
            raw, neutral = np.empty((80, n)), np.empty((80, n))
            for index, point in enumerate(points):
                values = np.sort(rng.uniform(size=n));tuples = by_job(point)
                order = [j for f in sorted(set(point['FA']), reverse=True) for j in point['JS'] if tuples[j, 0] == f]
                alternate = {'JS': order, **{name: [int(tuples[j, col]) for j in order] for col, name in enumerate(('FA', 'MA', 'WA'))}}
                assert physical_key(point) == physical_key(alternate)
                raw[index, point['JS']] = values;neutral[index, order] = values
            for kind, matrix in (('rawGlobalOrder', raw), ('neutralFactoryInterleaving', neutral)):
                cases.append({'case': len(cases), 'stem': stem, 'seed': seed, 'kind': kind, 'source': str(source), 'keys': matrix.tolist()})
    write_once(root / 'dependency-cases.json', cases)
    with (root / 'dependency-cases.tsv').open('x', encoding='ascii') as output:
        for case in cases:
            matrix = case['keys'];output.write(f'{case["case"]}\t{len(matrix[0])}\t{len(matrix)}\n')
            output.write('\n'.join('\t'.join(map(repr, row)) for row in matrix) + '\n')
    return cases


def expected_dependency(keys, first, second):
    keys = np.asarray(keys);probability = float(np.mean(keys[:, first] < keys[:, second]))
    entropy = 0. if probability in (0., 1.) else -(probability * math.log(probability) + (1 - probability) * math.log(1 - probability)) / math.log(2.)
    squared_distance = float(np.mean((keys[:, first] - keys[:, second]) ** 2))
    return (1 - entropy) * (1 - squared_distance)

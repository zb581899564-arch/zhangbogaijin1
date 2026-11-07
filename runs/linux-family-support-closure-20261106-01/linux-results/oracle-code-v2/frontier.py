"""Exact dyadic objectives and monotone Pareto dynamic programming with witnesses."""
from bisect import bisect_left
from itertools import product
import math


def objective_powers(records):
    powers = [0, 0, 0]
    for record in records:
        for k, value in enumerate(record['objectives']):
            assert math.isfinite(value) and value >= 0
            denominator = float(value).as_integer_ratio()[1]
            powers[k] = max(powers[k], denominator.bit_length() - 1)
    return powers


def encode(values, powers):
    result = []
    for value, power in zip(values, powers):
        numerator, denominator = float(value).as_integer_ratio()
        shift = power - (denominator.bit_length() - 1)
        assert shift >= 0
        result.append(numerator << shift)
    return tuple(result)


def decode(values, powers):
    return [math.ldexp(value, -power) for value, power in zip(values, powers)]


def pareto(points):
    """Lexicographic C/E/W sweep; Fenwick prefix minimum gives exact weak domination."""
    points = sorted(points)
    if not points:
        return []
    energies = sorted({p[1] for p in points})
    tree = [None] * (len(energies) + 1)
    output = []
    for point in points:
        index = bisect_left(energies, point[1]) + 1
        probe, minimum = index, None
        while probe:
            if tree[probe] is not None:
                minimum = tree[probe] if minimum is None else min(minimum, tree[probe])
            probe -= probe & -probe
        if minimum is not None and minimum <= point[2]:
            continue
        output.append(point)
        while index < len(tree):
            tree[index] = point[2] if tree[index] is None else min(tree[index], point[2])
            index += index & -index
    return output


def close(factories, powers):
    # max and addition are monotone: a dominated partial state can never become necessary.
    frontier = [(0, 0, 0, ())]
    stages = []
    for factory, records in enumerate(factories):
        local = [(*encode(r['objectives'], powers), index) for index, r in enumerate(records)]
        expanded = [(max(a[0], b[0]), a[1]+b[1], a[2]+b[2], a[3]+(b[3],))
                    for a in frontier for b in local]
        frontier = pareto(expanded)
        stages.append({'factory': factory, 'localRecords': len(records),
                       'expandedStates': len(expanded), 'retainedStates': len(frontier)})
    return frontier, stages


def engineering_checks():
    fixtures = [
        [[(1, 9, 1), (2, 4, 4), (3, 1, 9)]] * 3,
        [[(2, 1, 4), (2, 2, 3), (2, 3, 2)], [(1, 3, 2), (3, 1, 3)]],
        [[(1, 1, 1), (1, 1, 1), (2, 2, 2)], [(5, 3, 4), (4, 4, 3)]]]
    reports = []
    for values in fixtures:
        factories = [[{'objectives': list(v)} for v in records] for records in values]
        powers = objective_powers([r for f in factories for r in f])
        actual, stages = close(factories, powers)
        exhaustive = []
        for indices in product(*(range(len(f)) for f in factories)):
            chosen = [encode(factories[f][i]['objectives'], powers) for f, i in enumerate(indices)]
            exhaustive.append((max(p[0] for p in chosen), sum(p[1] for p in chosen),
                               sum(p[2] for p in chosen), indices))
        expected = {p[:3] for p in exhaustive if not any(
            q[:3] != p[:3] and all(q[k] <= p[k] for k in range(3)) for q in exhaustive)}
        assert {p[:3] for p in actual} == expected
        reports.append({'cartesian': len(exhaustive), 'frontier': len(actual), 'status': 'PASS'})
    return reports

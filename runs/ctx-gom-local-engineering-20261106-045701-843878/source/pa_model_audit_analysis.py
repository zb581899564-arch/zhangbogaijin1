"""Independent scipy tails, entropy-based MI and original-matrix mean-linkage checks; no search."""
import math
from collections import Counter

import numpy as np
from scipy.stats import binom

from run_long_budget_bridge import rows


def check_binomial(path):
    records = np.loadtxt(path, delimiter='\t'); worst = 0.
    for population, factories in sorted(set(map(tuple, records[:, :2].astype(int)))):
        selected = records[(records[:, 0] == population) & (records[:, 1] == factories)]
        assert len(selected) == population + 1 and np.array_equal(selected[:, 2], np.arange(population + 1))
        counts = selected[:, 2].astype(int); mean_floor = population // factories
        lower = binom.cdf(counts, population, 1. / factories)
        upper = binom.sf(counts, population, 1. / factories)
        expected = 1 - np.where(counts * factories > population,
            upper / binom.sf(mean_floor, population, 1. / factories),
            lower / binom.cdf(mean_floor, population, 1. / factories))
        error = float(abs(selected[:, 3] - expected).max()); worst = max(worst, error)
        assert error < 3e-12
    return {'tailValues': len(records), 'maximumError': worst}


def entropy(values):
    p = np.array(list(Counter(values).values()), dtype=float) / len(values)
    return -float(np.sum(p * np.log(p)))


def check_hierarchy(matrix, subsets):
    n = len(matrix); assert len(subsets) == 2 * n - 1 and subsets[:n] == [[j] for j in range(n)]
    active = [tuple([j]) for j in range(n)]; worst = 0.
    for subset in subsets[n:]:
        merged = tuple(subset); assert tuple(sorted(set(subset))) == merged
        children = [s for s in active if set(s).issubset(merged)]
        assert len(children) == 2 and tuple(sorted(children[0] + children[1])) == merged
        chosen = float(matrix[np.ix_(*children)].mean())
        best = max(float(matrix[np.ix_(a, b)].mean()) for i, a in enumerate(active) for b in active[i + 1:])
        worst = max(worst, abs(chosen - best)); assert abs(chosen - best) < 1e-12
        active = [s for s in active if s not in children] + [merged]
    assert active == [tuple(range(n))]
    return {'merges': n - 1, 'maximumChosenMeanDeficit': worst}


def analyze(folder):
    genomes = rows(folder / 'genomes.jsonl'); model, = rows(folder / 'model.jsonl'); receipt, = rows(folder / 'receipt.jsonl')
    assert receipt['status'] == 'COMPLETE' and len(genomes) == 80 and receipt['decoderCalls'] == 160
    factories = np.array([g['factoryByJob'] for g in genomes]); keys = np.array([g['keysByJob'] for g in genomes])
    p, n = factories.shape; count = model['factories']; records = np.loadtxt(folder / 'components.tsv', delimiter='\t')
    assert len(records) == n * (n - 1) // 2
    worst = 0.; matrix = np.zeros((n, n)); seen = set(); branches = Counter()
    for record in records:
        a, b = map(int, record[:2]); assert 0 <= a < b < n and (a, b) not in seen; seen.add((a, b))
        same = factories[:, a] == factories[:, b]; x = int(same.sum()); branches['attraction' if x * count > p else 'repulsion'] += 1
        ordering = float(np.mean(keys[same, a] < keys[same, b])) if x else 0
        order_information = 1 if ordering in (0, 1) else 1 + ordering * math.log2(ordering) + (1 - ordering) * math.log2(1 - ordering)
        internal = order_information * (1 - float(np.mean((keys[same, a] - keys[same, b]) ** 2))) if x else 0
        external = (entropy(factories[:, a]) + entropy(factories[:, b]) - entropy(list(zip(factories[:, a], factories[:, b])))) / math.log(count)
        stat = 1 - (binom.sf(x, p, 1 / count) / binom.sf(p // count, p, 1 / count) if x * count > p
                    else binom.cdf(x, p, 1 / count) / binom.cdf(p // count, p, 1 / count))
        full = stat * (2 / 3 + (1 / 3) * (internal if x * count > p else external))
        expected = np.array([full, stat, internal, external, x]); error = float(abs(expected - record[2:]).max())
        worst = max(worst, error); assert error < 3e-12
        matrix[a, b] = matrix[b, a] = record[2]
    tails = check_binomial(folder / 'binomial.tsv'); hierarchy = check_hierarchy(matrix, model['subsets'])
    fixtures, = rows(folder / 'fixtures.jsonl')
    assert abs(fixtures['singleFactory'][0] - .96) < 1e-12 and abs(fixtures['repulsion'][0] - 2/3) < 1e-12
    return {'componentPairs': len(records), 'maximumComponentError': worst, 'branchCounts': dict(branches),
            'binomial': tails, 'hierarchy': hierarchy, 'receipt': receipt,
            'modelSeconds': model['modelNanos'] / 1e9, 'hierarchySeconds': model['hierarchyNanos'] / 1e9,
            'scope': 'Engineering/model mathematics only; no performance or innovation evidence'}

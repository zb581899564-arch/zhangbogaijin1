"""Model rebuilt from the live reconstructed population, independent entropy and scipy formulas."""
from collections import Counter
import math

import numpy as np
from scipy.stats import binom

from pa_model_audit_analysis import check_hierarchy


def entropy(values):
    frequencies = Counter(values)
    return -sum((v / len(values)) * math.log(v / len(values)) for v in frequencies.values())


def check_model(event, population, catalog):
    f = np.array([[catalog[r][0] for r in point['resources']] for point in population])
    keys = np.array([point['keys'] for point in population]); size, n = f.shape
    factories = max(row[0] for row in catalog) + 1
    marginal = [entropy(f[:, j]) for j in range(n)]
    counts = np.arange(size + 1); cutoff = size // factories
    stat = 1 - np.where(counts * factories > size,
        binom.sf(counts, size, 1 / factories) / binom.sf(cutoff, size, 1 / factories),
        binom.cdf(counts, size, 1 / factories) / binom.cdf(cutoff, size, 1 / factories))
    expected = np.zeros((n, n)); observed = np.array(event['dependency']); assert observed.shape == (n, n)
    for a in range(n):
        for b in range(a + 1, n):
            same = f[:, a] == f[:, b]; x = int(same.sum())
            internal = 0.
            if x:
                p = float(np.mean(keys[same, a] < keys[same, b]))
                order = 1 if p in (0., 1.) else 1 + p * math.log2(p) + (1-p) * math.log2(1-p)
                internal = order * (1 - float(np.mean((keys[same, a] - keys[same, b])**2)))
            external = (marginal[a] + marginal[b] - entropy(list(zip(f[:, a], f[:, b])))) / math.log(factories)
            expected[a, b] = expected[b, a] = stat[x] * (2/3 + (1/3) * (internal if x*factories > size else external))
    error = float(abs(expected - observed).max()); assert error < 3e-12
    hierarchy = check_hierarchy(observed, event['subsets'])
    return {'pairs': n*(n-1)//2, 'maximumModelError': error, **hierarchy}

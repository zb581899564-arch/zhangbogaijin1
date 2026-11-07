"""Rebuild native cohort model matrices and validate each FOS merge independently."""
from collections import Counter
import hashlib
import json
import math

import numpy as np

from audit_core import require


CACHE = {}


def entropy(values):
    counts = Counter(values)
    return -sum((count / len(values)) * math.log(count / len(values))
                for count in counts.values())


def hierarchy(matrix, subsets):
    """Check each merge against original-matrix means; no Java priority queue."""
    size = len(matrix)
    require(len(subsets) == 2 * size - 1 and subsets[:size] == [[i] for i in range(size)],
            "FOS singleton coverage or length differs")
    active = {i: [i] for i in range(size)}
    sums = {(i, j): float(matrix[i, j]) for i in range(size) for j in range(i + 1, size)}
    worst = 0.0
    for index, group in enumerate(subsets[size:], size):
        require(group == sorted(set(group)), "FOS subset is not a sorted set")
        children = [i for i, values in active.items() if set(values).issubset(group)]
        require(len(children) == 2, "FOS merge has other than two active children")
        a, b = children
        require(sorted(active[a] + active[b]) == group, "FOS merge membership differs")
        scores = {pair: total / (len(active[pair[0]]) * len(active[pair[1]]))
                  for pair, total in sums.items()}
        deficit = max(scores.values()) - scores[tuple(sorted((a, b)))]
        require(abs(deficit) < 1e-12, "FOS merge is not maximum average linkage")
        worst = max(worst, abs(deficit))
        new = {tuple(sorted((i, index))): sums[tuple(sorted((a, i)))] +
               sums[tuple(sorted((b, i)))] for i in active if i not in (a, b)}
        sums = {pair: total for pair, total in sums.items() if a not in pair and b not in pair}
        sums.update(new)
        del active[a], active[b]
        active[index] = group
    require(list(active.values()) == [list(range(size))], "FOS root is incomplete")
    return worst


def expected_matrix(factories, keys, factory_count):
    size, jobs = factories.shape
    expected = np.zeros((jobs, jobs))
    marginal = [entropy(factories[:, j]) for j in range(jobs)]
    if factory_count > 1:
        counts, cutoff = np.arange(size + 1), size // factory_count
        probability = 1 / factory_count
        masses = [math.comb(size, count) * probability ** count * (1 - probability) ** (size - count)
                  for count in range(size + 1)]
        upper = np.array([math.fsum(masses[count + 1:]) for count in range(size + 1)])
        lower = np.array([math.fsum(masses[:count + 1]) for count in range(size + 1)])
        attraction, repulsion = upper / upper[cutoff], lower / lower[cutoff]
        statistic = 1 - np.where(counts * factory_count > size, attraction, repulsion)
    for a in range(jobs):
        for b in range(a + 1, jobs):
            same = factories[:, a] == factories[:, b]
            count = int(same.sum())
            internal = 0.0
            if count:
                probability = float(np.mean(keys[same, a] < keys[same, b]))
                order = 1 if probability in (0.0, 1.0) else 1 + probability * math.log2(probability) + (1 - probability) * math.log2(1 - probability)
                internal = order * (1 - float(np.mean((keys[same, a] - keys[same, b]) ** 2)))
            if factory_count == 1:
                value = internal
            else:
                external = (marginal[a] + marginal[b] - entropy(list(zip(factories[:, a], factories[:, b])))) / math.log(factory_count)
                value = statistic[count] * (2 / 3 + (1 / 3) *
                                           (internal if count * factory_count > size else external))
            expected[a, b] = expected[b, a] = value
    return expected


def check_model(event, population, catalog):
    jobs, slots, family = event["jobs"], event["slots"], event["family"]
    require(jobs == sorted(set(jobs)) and slots == sorted(set(slots)), "Unordered model indices")
    require(len(slots) == (80 if family < 0 else 5), "Model cohort size differs")
    require(event["subsets"] == [[jobs[j] for j in mask] for mask in event["localSubsets"]],
            "Local/global FOS mapping differs")
    members = [population[i] for i in slots]
    signature = hashlib.sha256(json.dumps([event, [[p["resources"], p["keys"]] for p in members]],
                                         sort_keys=True).encode()).hexdigest()
    if signature in CACHE:
        return dict(CACHE[signature], reusedExactMath=True)
    factories = np.array([[catalog["tuples"][p["resources"][j]][0] for j in jobs] for p in members])
    keys = np.array([[p["keys"][j] for j in jobs] for p in members])
    if family < 0:
        require(jobs == list(range(catalog["jobs"])) and event["factory"] == -1,
                "Free model omitted jobs or changed factory marker")
    else:
        require(np.all(factories == event["factory"]), "Fixed model crosses a factory")
        expected_jobs = [j for j in range(catalog["jobs"])
                         if catalog["tuples"][members[0]["resources"][j]][0] == event["factory"]]
        require(jobs == expected_jobs, "Fixed model omitted factory jobs")
    observed = np.asarray(event["dependency"], dtype=float)
    expected = expected_matrix(factories, keys, catalog["factories"] if family < 0 else 1)
    require(observed.shape == expected.shape and np.isfinite(observed).all(), "Invalid model matrix")
    error = float(np.max(np.abs(expected - observed)))
    require(error < 3e-12, "Dependency matrix differs from independent entropy/binomial math")
    result = dict(pairs=len(jobs) * (len(jobs) - 1) // 2, maximumModelError=error,
                  maximumChosenMeanDeficit=hierarchy(expected, event["localSubsets"]))
    CACHE[signature] = result
    return dict(result, reusedExactMath=False)

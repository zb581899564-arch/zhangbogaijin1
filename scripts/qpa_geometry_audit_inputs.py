"""Independent neutral-view physics, Java RNG and linkage checks; no objective API."""
import csv
import hashlib
import struct

import numpy as np

from qpa_state_checks import hierarchy
from run_long_budget_bridge import rows


class JavaRandom:
    def __init__(self, seed):
        self.state = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def bits(self, count):
        self.state = (self.state * 0x5DEECE66D + 11) & ((1 << 48) - 1)
        return self.state >> (48 - count)

    def double(self):
        return ((self.bits(26) << 27) + self.bits(27)) / (1 << 53)

    def integer(self, bound):
        if bound & (bound - 1) == 0:
            return (bound * self.bits(31)) >> 31
        while True:
            bits = self.bits(31)
            value = bits % bound
            if bits - value + bound - 1 < (1 << 31):
                return value


def physical(point, factories):
    return tuple(tuple((j, m, w) for j, f, m, w in
                       zip(point['JS'], point['FA'], point['MA'], point['WA']) if f == factory)
                 for factory in range(factories))


def physical_hash(point, factories):
    values = [len(point['JS']), factories]
    for factory, chain in enumerate(physical(point, factories)):
        values.extend((factory, len(chain)))
        values.extend(v for entry in chain for v in entry)
    return hashlib.sha256(struct.pack('>' + 'i' * len(values), *values)).hexdigest()


def views(path):
    result = {}
    with path.open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            key = row['population'], row['variant']
            points = result.setdefault(key, [])
            assert int(row['slot']) == len(points)
            point = {name: list(map(int, row[name].split(','))) for name in ('JS', 'FA', 'MA', 'WA')}
            point.update(objectives=list(map(float, row['objectives'].split(','))),
                         knownFE=int(row['knownFE']), role=row['role'])
            points.append(point)
    assert all(len(points) == 100 for points in result.values())
    return result


def reencode(points, tuples, factories, seed):
    ids = {tuple(value): index for index, value in enumerate(tuples)}
    rng = JavaRandom(seed)
    result = []
    for point in points:
        resources = [None] * len(point['JS'])
        keys = [None] * len(resources)
        for j, f, m, w in zip(point['JS'], point['FA'], point['MA'], point['WA']):
            resources[j] = ids[f, m, w]
        for chain in physical(point, factories):
            values = sorted(rng.double() for _ in chain)
            assert values[0] > 0 and len(set(values)) == len(values)
            for (job, _, _), key in zip(chain, values):
                keys[job] = key
        result.append(dict(resources=resources, keys=keys))
    return result


def check_models(root, stem, plan, execution):
    data = views(root / (stem + '-views.tsv'))
    models = {(m['population'], m['variant']): m for m in rows(root / stem / 'models.jsonl')}
    catalog, = rows(__import__('pathlib').Path(plan['sourceEngineering']) / stem / 'main/catalog.jsonl')
    factories = catalog['factories']
    assert set(data) == set(models) and len(models) == 44
    statistics = []
    pa_hierarchies = set()
    for (population, variant), points in data.items():
        original = data[population, 'ORIGINAL']
        model = models[population, variant]
        baseline = models[population, 'ORIGINAL']
        for a, b in zip(points, original):
            n = len(a['JS'])
            assert sorted(a['JS']) == list(range(n))
            assert all(len(a[k]) == n for k in ('FA', 'MA', 'WA'))
            assert physical(a, factories) == physical(b, factories)
            assert (a['objectives'], a['knownFE'], a['role']) == (b['objectives'], b['knownFE'], b['role'])
        position = np.argsort(np.array([p['JS'] for p in points]))
        matrix = 1 - np.abs(position[:, :, None] - position[:, None, :]).sum(axis=0)/(100 * (n-1))
        np.fill_diagonal(matrix, 0.)
        error = float(np.abs(matrix - np.array(model['qpaAffinity'])).max())
        assert error < 1e-12
        deficit = hierarchy(matrix, model['qpaFullSubsets'])
        assert model['qpaActiveSubsets'] == [g for g in model['qpaFullSubsets'] if len(g) < round((n/12)*10)]
        genes = reencode(points, catalog['tuples'], factories, execution['paNoiseSeed'])
        assert genes == model['paGenes'] == baseline['paGenes']
        for a, b in zip(genes, model['paGenes']):
            assert struct.pack('>' + 'd'*n, *a['keys']) == struct.pack('>' + 'd'*n, *b['keys'])
        assert model['paAffinity'] == baseline['paAffinity'] and model['paSubsets'] == baseline['paSubsets']
        if population not in pa_hierarchies:
            hierarchy(np.array(model['paAffinity']), model['paSubsets'])
            pa_hierarchies.add(population)
        old = {tuple(g) for g in baseline['qpaActiveSubsets'] if len(g) > 1}
        new = {tuple(g) for g in model['qpaActiveSubsets'] if len(g) > 1}
        statistics.append(dict(population=population, variant=variant,
            maximumAffinityError=error, maximumMeanMergeDeficit=deficit,
            nonSingletonFOSJaccard=len(old & new)/len(old | new) if old | new else 1.,
            maximumQpaAffinityChange=float(np.abs(matrix-np.array(baseline['qpaAffinity'])).max())))
    return data, models, catalog, statistics

"""Physical changes, factory deltas and archive coverage without any decoding."""
from collections import Counter
import numpy as np
from common import FACTORY


def factory_order(row, factory):
    return [j for j, f in zip(row['JS'], row['FA']) if f == factory]


def physical_signature(row):
    nfactories = len(row['factoryMakespan'])
    return (tuple(row['resources']), tuple(tuple(factory_order(row, f)) for f in range(nfactories)))


def weakly_covered(background, obj):
    return bool(np.any(np.all(background <= np.asarray(obj), axis=1)))


def dominates(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def inversions(before, after):
    positions = {j: i for i, j in enumerate(before)}
    ranks = [positions[j] for j in after]
    return sum(a > b for i, a in enumerate(ranks) for b in ranks[i + 1:])


def describe(parent, candidate, catalog):
    changed = [j for j, (a, b) in enumerate(zip(parent['resources'], candidate['resources'])) if a != b]
    machine = [j for j in changed if catalog[parent['resources'][j]]['machine'] != catalog[candidate['resources'][j]]['machine']]
    worker = [j for j in changed if catalog[parent['resources'][j]]['worker'] != catalog[candidate['resources'][j]]['worker']]
    orders = []
    for f in range(len(parent['factoryMakespan'])):
        old, new = factory_order(parent, f), factory_order(candidate, f)
        assert set(old) == set(new), 'FA changed'
        if old != new:
            orders.append(dict(factory=f, inversions=inversions(old, new)))
    affected = sorted({catalog[parent['resources'][j]]['factory'] for j in changed} |
                      {r['factory'] for r in orders})
    parent_obj, obj = parent['objectives'], candidate['objectives']
    delta = [b - a for a, b in zip(parent_obj, obj)]
    critical = [f for f, v in enumerate(parent['factoryMakespan']) if v == max(parent['factoryMakespan'])]
    local = [{k: candidate[k][f] - parent[k][f] for k in FACTORY} | {'factory': f} for f in affected]
    for k in FACTORY:
        for f, (old, new) in enumerate(zip(parent[k], candidate[k])):
            assert f in affected or old == new, 'Unchanged physical factory changed objectives'
    expected = [max(candidate['factoryMakespan']), sum(candidate['factoryEnergy']), sum(candidate['factoryCost'])]
    assert np.allclose(expected, obj, rtol=1e-13, atol=1e-9)
    return dict(resourceJobs=changed, machineJobs=machine, workerJobs=worker, orderChanges=orders,
                affectedFactories=affected, touchesCritical=bool(set(affected) & set(critical)),
                criticalFactories=critical, parentDominates=dominates(parent_obj, obj),
                improvesParent=dominates(obj, parent_obj), objectiveDelta=delta, factoryDelta=local,
                physicalNoop=not affected, resourceOnly=bool(changed) and not orders,
                orderOnly=bool(orders) and not changed, resourceAndOrder=bool(orders) and bool(changed))


def summarize_features(records):
    counts = Counter()
    for r in records:
        for key in ('accepted', 'fresh', 'a0Novel', 'finalSurvivor', 'parentDominates', 'improvesParent',
                    'touchesCritical', 'physicalNoop', 'resourceOnly', 'orderOnly', 'resourceAndOrder'):
            counts[key] += bool(r[key])
        counts['role.' + r['role']] += 1
        counts['factory.' + ','.join(map(str, r['affectedFactories']))] += 1
        counts['deltaSigns.' + ','.join('+' if x > 1e-8 else '-' if x < -1e-8 else '0' for x in r['objectiveDelta'])] += 1
    counts['n'] = len(records)
    return dict(counts)

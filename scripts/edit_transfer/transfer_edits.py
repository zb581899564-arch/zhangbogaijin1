"""Literal edit transfer and ordinary controls matched by actual edited fields."""
import hashlib
import random
from transfer_common import encode, fa_map, physical


def apply_source(receiver, source, mask):
    resources, keys = list(receiver['resources']), list(receiver['keys'])
    for index, job in enumerate(source['jobs']):
        if mask & (1 << index):
            resources[job] = source['child']['resources'][job]
        if mask & (1 << (index + 2)):
            keys[job] = source['child']['keys'][job]
    return encode(resources, keys, source['catalog'])


def changes(receiver, child):
    return dict(resources=[j for j, (a, b) in enumerate(zip(receiver['resources'], child['resources'])) if a != b],
                keys=[j for j, (a, b) in enumerate(zip(receiver['keys'], child['keys'])) if a != b])


def control_seed(source_id, receiver_id, replicate):
    label = f'EDIT_TRANSFER_V1/166110601/{source_id}/{receiver_id}/{replicate}'
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], 'big')


def ordinary(receiver, pruned, source, replicate):
    seed = control_seed(source['id'], receiver['id'], replicate)
    rng = random.Random(seed)
    active = changes(receiver, pruned)
    resources, keys = list(receiver['resources']), list(receiver['keys'])
    factories = fa_map(receiver)
    for job in active['resources']:
        eligible = [i for i, item in enumerate(source['catalog'])
                    if item['factory'] == factories[job] and i != resources[job]]
        assert eligible, (source['id'], job)
        resources[job] = rng.choice(eligible)
    for job in active['keys']:
        value = rng.random()
        while value == keys[job]:
            value = rng.random()
        keys[job] = value
    child = encode(resources, keys, source['catalog'])
    assert changes(receiver, child) == active
    return child, seed


def displacement(receiver, child):
    inversions = 0
    for factory in range(max(receiver['FA']) + 1):
        old = [j for j, f in zip(receiver['JS'], receiver['FA']) if f == factory]
        new = [j for j, f in zip(child['JS'], child['FA']) if f == factory]
        ranks = {j: i for i, j in enumerate(new)}
        inversions += sum(ranks[a] > ranks[b] for i, a in enumerate(old) for b in old[i + 1:])
    return dict(factoryOrderInversions=inversions, neutralPhysical=physical(receiver) == physical(child))

"""Independent strict/equal trace reconstruction and outcome-blind neutral donor exposure selection."""
from collections import Counter, defaultdict
import json
import random

from run_long_budget_bridge import rows
from pa_population_replay import Replay
from pa_population_state_checks import physical, snapshot, vectors


def stored(point):
    return {k: point[k] for k in ('id', 'paidFE', 'role', 'resources', 'keys', 'objectives')}


def mixed(parent, donor, mask, catalog):
    resources, keys = parent['resources'].copy(), parent['keys'].copy()
    for job in mask:
        resources[job], keys[job] = donor['resources'][job], donor['keys'][job]
    missing = len({catalog[r][0] for r in resources}) != max(t[0] for t in catalog) + 1
    if missing:
        resources, keys = parent['resources'].copy(), parent['keys'].copy()
    return {'resources': resources, 'keys': keys, 'unscored': True}, missing


class NeutralReplay(Replay):
    def __init__(self, catalog, equal):
        super().__init__(catalog, boundary_equal=equal)
        self.tags, self.cases, self.bridges, self.initial = {}, [], Counter(), []

    def event(self, event):
        if event['kind'] == 'reencode' and event['slot'] == 0:
            self.tags.clear()  # No cross-generation rollback in incompatible randomized coordinates.
        super().event(event)
        if event['kind'] == 'initial':
            self.initial.append(dict(zip(('JS', 'FA', 'MA', 'WA'), vectors(event, self.catalog)), objectives=event['objectives']))

    def mix(self, event):
        parent, donor = self.population[event['slot']], self.population[event['donorSlot']]
        tag = self.tags.get(donor['id']) if event['role'] == 'CENTER' else None
        prior_archive = self.archive.copy() if tag else None
        super().mix(event)
        if tag:
            self.bridges['neutralTaggedCenterReads'] += 1
            mask = self.subsets[event['subset']]
            alternative, fallback = mixed(parent, tag['before'], mask, self.catalog)
            if physical(alternative, self.catalog) != physical(event, self.catalog):
                self.bridges['physicallyExposedCenterReads'] += 1
                self.cases.append({'generation': event['generation'], 'receiverSlot': event['slot'], 'paidFE': event['paidFE'],
                    'donorSlot': event['donorSlot'], 'subset': mask, 'actualAccepted': event['accepted'],
                    'sourceBridge': tag, 'actualDonor': stored(donor), 'receiver': stored(parent), 'actualChild': stored(event),
                    'rollbackChild': alternative, 'rollbackFallback': fallback, 'actualFallback': event['fallback'],
                    'priorArchive': prior_archive.tolist()})
        if not event['accepted']:
            return
        same_genes = event['resources'] == parent['resources'] and event['keys'] == parent['keys']
        if same_genes:
            if parent['id'] in self.tags:
                self.tags[event['id']] = self.tags[parent['id']]
            return
        target = {'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}.get(event['role'])
        if target is not None and event['objectives'][target] == parent['objectives'][target] and physical(event, self.catalog) != physical(parent, self.catalog):
            assert self.boundary_equal
            self.bridges['acceptedPhysicalNeutral.'+event['role']] += 1
            self.tags[event['id']] = {'paidFE': event['paidFE'], 'generation': event['generation'],
                                      'role': event['role'], 'before': stored(parent), 'after': stored(event)}


def reconstruct(folder):
    catalog, = rows(folder/'catalog.jsonl'); receipt, = rows(folder/'receipt.jsonl')
    check = NeutralReplay(catalog['tuples'], receipt['boundaryEqual'])
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            check.event(json.loads(line))
    assert receipt['status'] == 'COMPLETE' and receipt['successfulFE'] == receipt['attemptedFE'] == check.paid == receipt['paidFullTimelineQA']
    assert receipt['failedFE'] == 0 and receipt['paidSHA256'] == check.digest.hexdigest()
    assert receipt['neutralFullTimelineQA'] == check.neutral == 200 and receipt['fees'] == dict(check.fees)
    assert receipt['decoder']['dynamic.evaluations'] == check.paid
    assert receipt['completedGenerations'] == check.generations == 2 and receipt['completedPrograms'] == check.programs == 200
    for recorded, actual in zip(receipt['lastPopulation'], check.population):
        snapshot(recorded, actual)
    expected = sorted(map(tuple, check.archive.tolist()))
    assert sorted(map(tuple, receipt['internalArchive'])) == expected
    assert sorted(tuple(point['objectives']) for point in receipt['lastValidFront']) == expected
    return check, catalog, receipt


def select(check, seed, per_generation):
    by_generation = defaultdict(list)
    for case in check.cases:
        by_generation[case['generation']].append(case)
    selected = []
    for generation in (1, 2):
        available = by_generation[generation]
        picked = random.Random(seed+generation).sample(range(len(available)), min(per_generation, len(available)))
        selected.extend(available[i] for i in sorted(picked))
    selected.sort(key=lambda case: case['paidFE'])
    for index, case in enumerate(selected):
        case['case'] = index
    eligibility = [{k: case[k] for k in ('generation', 'receiverSlot', 'paidFE', 'donorSlot', 'subset')} for case in check.cases]
    return selected, eligibility


def write_pairs(path, cases, catalog):
    with path.open('x', encoding='utf-8') as stream:
        for case in cases:
            for branch, key in (('ACTUAL', 'actualChild'), ('ROLLBACK', 'rollbackChild')):
                expected = ','.join(repr(v) for v in case[key]['objectives']) if branch == 'ACTUAL' else '-'
                values = [str(case['case']), branch, expected]
                values.extend(','.join(map(str, v)) for v in vectors(case[key], catalog))
                stream.write('\t'.join(values)+'\n')

"""Stream all paid attempts from source states/FOS/donor identities, with independent decisions and hashes."""
from collections import Counter
import hashlib
import json

import numpy as np

from run_long_budget_bridge import read, rows, write_once
from pa_population_model_checks import check_model
from pa_population_state_checks import identity, paid_bytes, physical, snapshot, offer


class Replay:
    def __init__(self, catalog):
        self.catalog = catalog; self.population = []; self.archive = np.empty((0,3)); self.fees = Counter()
        self.paid = 0; self.neutral = 0; self.models = []; self.generation = 0; self.programs = self.generations = 0
        self.accepted = self.fallbacks = self.unchanged = self.fresh_reads = self.changed_reads = self.duplicates = 0
        self.accepted_ids = set(); self.changed_ids = set(); self.raw_hashes = set(); self.subsets = None
        self.digest = hashlib.sha256(); self.prefixes = {}; self.previous_state_id = 0
        self.used_subsets = set(); self.current_slot = -1; self.phase = 'INITIALIZATION'
        self.reencoded_slots = 0

    def birth(self, event):
        assert event['id'] == self.previous_state_id + 1; self.previous_state_id = event['id']
        assert event['hash'] == identity(event)

    def paid_event(self, event):
        self.paid += 1; assert event['paidFE'] == self.paid
        self.digest.update(paid_bytes(event, self.catalog, self.paid))
        raw_hash = hashlib.sha256(paid_bytes(event, self.catalog, 0)).hexdigest()
        assert raw_hash == event['rawPaidHash']
        self.duplicates += raw_hash in self.raw_hashes; self.raw_hashes.add(raw_hash)
        if self.paid in (1,2,101,139,4000): self.prefixes[self.paid] = self.digest.copy().hexdigest()
        self.fees['role.' + event['role']] += 1; self.archive = offer(self.archive, event)

    def event(self, event):
        kind = event['kind']
        if kind == 'initial':
            assert event['slot'] == len(self.population) and self.generation == 0
            self.birth(event); self.paid_event(event); self.population.append(event); self.fees['initialization'] += 1
        elif kind == 'reencode':
            slot = event['slot']
            if slot == 0:
                assert len(self.population) == 100 and event['generation'] == self.generation + 1
                self.generation += 1; self.accepted_ids.clear(); self.changed_ids.clear(); self.phase = 'REENCODING'
                self.reencoded_slots = 0
            assert slot == self.reencoded_slots; self.reencoded_slots += 1
            before = self.population[slot]
            assert event['beforeId'] == before['id'] and event['beforeHash'] == before['hash']
            assert event['paidFE'] == before['paidFE'] and event['objectives'] == before['objectives'] and event['role'] == before['role']
            assert event['resources'] == before['resources'] and physical(event, self.catalog) == physical(before, self.catalog)
            self.birth(event); self.population[slot] = event; self.neutral += 1
        elif kind == 'model':
            assert event['generation'] == self.generation and self.phase == 'REENCODING'
            assert self.reencoded_slots == len(event['population']) == len(self.population) == 100
            for recorded, current in zip(event['population'], self.population): snapshot(recorded, current)
            self.models.append(check_model(event, self.population, self.catalog)); self.subsets = event['subsets']; self.phase = 'MIXING'
            self.current_slot = -1; self.used_subsets.clear()
        elif kind == 'step':
            self.mix(event)
        elif kind == 'programEnd':
            assert event['slot'] == self.current_slot and len(self.used_subsets) == len(self.subsets)
            snapshot(event['result'], self.population[self.current_slot]); self.programs += 1
        elif kind == 'generationEnd':
            assert self.current_slot == 99 and self.programs == self.generation * 100
            assert len(event['population']) == len(self.population) == 100
            for recorded, current in zip(event['population'], self.population): snapshot(recorded, current)
            self.generations += 1; self.phase = 'GENERATION_COMPLETE'
        else:
            raise AssertionError('Unknown event ' + kind)

    def mix(self, event):
        assert self.phase == 'MIXING' and event['generation'] == self.generation
        slot, donor_slot = event['slot'], event['donorSlot']; assert slot != donor_slot and 0 <= donor_slot < 100
        if slot != self.current_slot:
            assert slot == self.current_slot + 1 and event['step'] == 0
            self.current_slot = slot; self.used_subsets.clear()
        assert event['step'] == len(self.used_subsets) and event['subset'] not in self.used_subsets
        self.used_subsets.add(event['subset']); subset = self.subsets[event['subset']]
        parent, donor = self.population[slot], self.population[donor_slot]
        assert event['parentId'] == parent['id'] and event['parentHash'] == parent['hash']
        assert event['donorId'] == donor['id'] and event['donorHash'] == donor['hash']
        assert event['parentObjectives'] == parent['objectives'] and event['role'] == parent['role']
        resources, keys = parent['resources'].copy(), parent['keys'].copy()
        for job in subset: resources[job], keys[job] = donor['resources'][job], donor['keys'][job]
        missing = len({self.catalog[r][0] for r in resources}) != max(t[0] for t in self.catalog) + 1
        assert event['fallback'] == missing
        if missing: resources, keys = parent['resources'], parent['keys']
        event['resources'], event['keys'] = resources, keys
        if missing: assert event['objectives'] == parent['objectives']
        if len(subset) == len(resources): assert event['objectives'] == donor['objectives']
        self.birth(event); self.paid_event(event)
        obj, old = event['objectives'], parent['objectives']
        target = {'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}.get(event['role'])
        accept = (all(a <= b for a,b in zip(obj,old)) or not event['archiveDominated']) if target is None else obj[target] < old[target]
        assert event['accepted'] == accept
        fresh = donor['id'] in self.accepted_ids; changed = donor['id'] in self.changed_ids
        assert event['donorAcceptedThisGeneration'] == fresh and event['donorChangedThisGeneration'] == changed
        self.fresh_reads += fresh; self.changed_reads += changed
        if accept:
            self.population[slot] = event; self.accepted_ids.add(event['id']); self.accepted += 1
            if event['hash'] != parent['hash']: self.changed_ids.add(event['id'])
        self.fallbacks += missing; self.unchanged += event['hash'] == parent['hash']; self.fees['mixing'] += 1


def analyze(folder):
    catalog, = rows(folder / 'catalog.jsonl'); receipt, = rows(folder / 'receipt.jsonl'); replay = Replay(catalog['tuples'])
    with (folder / 'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            if line.strip(): replay.event(json.loads(line))
    assert receipt['status'] == 'COMPLETE' and receipt['successfulFE'] == receipt['attemptedFE'] == replay.paid == receipt['paidFullTimelineQA']
    assert receipt['failedFE'] == 0 and receipt['paidSHA256'] == replay.digest.hexdigest()
    assert receipt['reencodingFullTimelineQA'] == replay.neutral
    assert receipt['completeRawDuplicates'] == replay.duplicates and receipt['fees'] == dict(replay.fees)
    for key, value in [('accepted',replay.accepted),('fallbacks',replay.fallbacks),('unchangedStoredStates',replay.unchanged),
                       ('currentGenerationDonorReads',replay.fresh_reads),('changedCurrentGenerationDonorReads',replay.changed_reads),
                       ('generation',replay.generation),('completedGenerations',replay.generations),('completedPrograms',replay.programs),('phase',replay.phase)]:
        assert receipt[key] == value, (key,receipt[key],value)
    assert len(receipt['lastPopulation']) == len(replay.population)
    for saved, actual in zip(receipt['lastPopulation'],replay.population): snapshot(saved, actual)
    expected = sorted(map(tuple,replay.archive.tolist()))
    assert sorted(map(tuple,receipt['internalArchive'])) == expected
    assert sorted(tuple(point['objectives']) for point in receipt['lastValidFront']) == expected
    result = {'allPaidStatesAndAcceptanceReconstructed':True,'successfulFE':replay.paid,'neutralFullQA':replay.neutral,
        'programs':replay.programs,'generations':replay.generations,'modelChecks':replay.models,'duplicates':replay.duplicates,
        'currentGenerationDonorReads':replay.fresh_reads,'changedCurrentGenerationDonorReads':replay.changed_reads,
        'prefixPaidSHA256':{str(k):v for k,v in replay.prefixes.items() if v is not None},'paidSHA256':receipt['paidSHA256'],
        'defaultMainlineChanged':False,'performanceEvidence':False,'goalAchieved':False}
    write_once(folder / 'independent-replay.json', result); return result

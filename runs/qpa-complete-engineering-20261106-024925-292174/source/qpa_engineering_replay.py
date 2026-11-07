"""Streaming independent reconstruction of the synchronous, two-phase paid lifecycle."""
from collections import Counter
import hashlib
import json

import numpy as np

from run_long_budget_bridge import rows
from pa_population_state_checks import offer, snapshot
from qpa_state_checks import child, identity, paid_bytes, model_check


class Replay:
    def __init__(self, catalog, receipt):
        self.catalog, self.receipt = catalog, receipt
        self.states, self.population, self.parents, self.offspring = {}, [], [], []
        self.archive = np.empty((0, 3)); self.digest = hashlib.sha256(); self.prefix = {}
        self.raw, self.fees, self.counts = set(), Counter(), Counter()
        self.working = None; self.generation = 0; self.completed = 0; self.slot = 0
        self.mask_order, self.last_step, self.models = [], None, []
        self.wanted = {1, 2, 100, 101, 102, receipt['successfulFE'] - 1, receipt['successfulFE']}

    def paid(self, event, point, initial=False):
        fe = len(self.states) + 1
        assert point['id'] == point['paidFE'] == fe and point['hash'] == identity(point)
        assert sorted(point['positions']) == list(range(self.catalog['jobs']))
        assert len(point['resources']) == self.catalog['jobs']
        assert all(0 <= r < len(self.catalog['tuples']) for r in point['resources'])
        assert len({self.catalog['tuples'][r][0] for r in point['resources']}) == self.catalog['factories']
        raw = hashlib.sha256(paid_bytes(point, self.catalog['tuples'], 0)).hexdigest()
        assert event['rawPaidHash'] == raw
        self.counts['duplicates'] += raw in self.raw; self.raw.add(raw)
        self.digest.update(paid_bytes(point, self.catalog['tuples'], fe))
        if fe in self.wanted:
            self.prefix[str(fe)] = self.digest.copy().hexdigest()
        self.archive = offer(self.archive, event); self.states[fe] = point
        self.fees['initialization' if initial else 'mixing'] += 1
        self.fees['role.' + point['role']] += 1
        return fe

    def initial(self, event):
        assert not self.parents and self.generation == 0 and event['slot'] == len(self.population)
        slot = event['slot']; assert slot < 100
        role = 'MAKESPAN' if slot < 15 else 'CENTER' if slot < 70 else 'ENERGY' if slot < 85 else 'WORKER_COST'
        assert event['role'] == role
        self.population.append(self.paid(event, event, True))

    def model(self, event):
        assert len(self.population) == 100 and self.completed == self.generation
        assert event['generation'] == self.generation + 1
        for value, state_id in zip(event['parents'], self.population):
            snapshot(value, self.states[state_id])
        self.models.append(model_check(event, self.states, self.population))
        self.generation += 1; self.parents = self.population.copy(); self.offspring = []
        self.active = event['activeSubsets']; self.slot = 0; self.working = self.parents[0]
        self.mask_order = []; self.last_step = None

    def step(self, event):
        assert event['generation'] == self.generation and event['slot'] == self.slot == len(self.offspring)
        donor = self.states[self.parents[event['donorSlot']]]
        assert (event['donorId'], event['donorHash']) == (donor['id'], donor['hash'])
        parent = self.states[self.working]
        assert (event['parentId'], event['parentHash'], event['parentObjectives']) == (parent['id'], parent['hash'], parent['objectives'])
        assert event['role'] == parent['role'] == self.states[self.parents[self.slot]]['role']
        if event['phase'] == 1:
            assert self.last_step is None or self.last_step['phase'] == 2
            assert event['step'] == len(self.mask_order) and event['subset'] not in self.mask_order
            self.mask_order.append(event['subset'])
        else:
            assert self.last_step is not None and self.last_step['phase'] == 1 and event['phase'] == 2
            for key in ('step', 'subset', 'donorSlot', 'donorId', 'donorHash'):
                assert event[key] == self.last_step[key]
        mask = self.active[event['subset']]
        value = child(event, parent, donor, mask, self.catalog['tuples'], self.catalog['factories'])
        self.paid(event, value)
        if parent['role'] == 'CENTER':
            accept = all(a <= b for a, b in zip(value['objectives'], parent['objectives'])) or not event['archiveDominated']
        else:
            objective = {'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}[parent['role']]
            accept = value['objectives'][objective] <= parent['objectives'][objective]
        assert event['accepted'] == accept
        self.counts['accepted'] += accept; self.counts['fallbacks'] += event['fallback']
        self.counts['unchanged'] += value['hash'] == parent['hash']; self.fees['phase.' + str(event['phase'])] += 1
        if accept:
            self.working = value['id']
        self.last_step = event

    def program_end(self, event):
        assert event['generation'] == self.generation and event['slot'] == self.slot
        assert self.last_step['phase'] == 2 and sorted(self.mask_order) == list(range(len(self.active)))
        snapshot(event['result'], self.states[self.working]); self.offspring.append(self.working)
        self.counts['programs'] += 1; self.slot += 1; self.mask_order = []; self.last_step = None
        if self.slot < 100:
            self.working = self.parents[self.slot]

    def generation_end(self, event):
        assert event['generation'] == self.generation and len(self.offspring) == 100
        self.population = self.offspring.copy(); self.completed += 1
        self.check_list(event['population'], self.population)

    def check_list(self, records, states):
        assert len(records) == len(states)
        for record, state_id in zip(records, states):
            snapshot(record, self.states[state_id])

    def finish(self):
        receipt = self.receipt; paid = len(self.states)
        assert receipt['status'] == 'COMPLETE' and receipt['error'] is None
        assert paid == receipt['successfulFE'] == receipt['attemptedFE'] == receipt['paidFullTimelineQA']
        assert receipt['failedFE'] == receipt['neutralFullTimelineQA'] == 0
        assert receipt['decoder']['dynamic.evaluations'] == paid
        assert receipt['paidSHA256'] == self.digest.hexdigest() and receipt['fees'] == dict(self.fees)
        assert receipt['completeRawDuplicates'] == self.counts['duplicates']
        for key in ('accepted', 'fallbacks'):
            assert receipt[key] == self.counts[key]
        assert receipt['unchangedStoredStates'] == self.counts['unchanged']
        assert receipt['completedPrograms'] == self.counts['programs'] and receipt['completedGenerations'] == self.completed
        self.check_list(receipt['lastPopulation'], self.population)
        self.check_list(receipt['frozenParents'], self.parents); self.check_list(receipt['partialOffspring'], self.offspring)
        if not self.parents:
            assert receipt['working'] is None
        else:
            # An FE cutoff between programs retains the just-completed working state, before entering the next owner.
            actual_work = self.working if self.last_step is not None or self.slot == 100 else self.offspring[-1] if self.offspring else self.parents[0]
            snapshot(receipt['working'], self.states[actual_work])
        assert receipt['internalArchive'] == self.archive.tolist()
        assert {tuple(p['objectives']) for p in receipt['lastValidFront']} == set(map(tuple, self.archive))
        assert receipt['diagnostics']['initialization.evaluations'] == self.fees['initialization']
        assert receipt['diagnostics']['global.evaluations'] == self.fees['mixing']
        return {'passed': True, 'paidReconstructed': paid, 'paidSHA256': self.digest.hexdigest(), 'prefixSHA256': self.prefix,
                'completeGenerations': self.completed, 'completePrograms': self.counts['programs'],
                'modelChecks': self.models, 'counts': dict(self.counts), 'extraSearchFE': 0, 'decoderCalls': 0}


def replay(folder):
    catalog, = rows(folder/'catalog.jsonl'); receipt, = rows(folder/'receipt.jsonl')
    check = Replay(catalog, receipt)
    handlers = {'initial': check.initial, 'model': check.model, 'step': check.step,
                'programEnd': check.program_end, 'generationEnd': check.generation_end}
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line); handlers[event['kind']](event)
    return check.finish()

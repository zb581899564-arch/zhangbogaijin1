"""Descriptive, zero-FE audit of already-paid two-generation physical changes; no retuning."""
from collections import Counter
import json

from run_long_budget_bridge import ROOT, rows, write_once
from qpa_engineering_replay import Replay
from qpa_state_checks import vectors

ENGINE = ROOT/'runs/qpa-complete-engineering-20261106-024925-292174'


def physical(point, catalog):
    js, fa, ma, wa = vectors(point, catalog['tuples'])
    return tuple(tuple((j, m, w) for j, f, m, w in zip(js, fa, ma, wa) if f == factory)
                 for factory in range(catalog['factories']))


class PhysicalReplay(Replay):
    def __init__(self, catalog, receipt):
        super().__init__(catalog, receipt); self.groups = {}; self.signatures = {}; self.nuisance = []

    def signature(self, point):
        if point['id'] not in self.signatures:
            self.signatures[point['id']] = physical(point, self.catalog)
        return self.signatures[point['id']]

    def step(self, event):
        parent = self.states[self.working]; super().step(event); value = self.states[event['id']]
        group = self.groups.setdefault(str(event['phase']), Counter()); group['paid'] += 1
        same_genes = parent['resources'] == value['resources'] and parent['positions'] == value['positions']
        same_physical = self.signature(parent) == self.signature(value)
        resource_change = parent['resources'] != value['resources']
        if same_physical:
            assert parent['objectives'] == value['objectives']
        group['sameRawGenome'] += same_genes
        group['samePhysicalSchedule'] += same_physical
        group['rawChangedButPhysicalSame'] += not same_genes and same_physical
        group['resourceChanged'] += resource_change
        group['physicalChanged'] += not same_physical
        group['accepted'] += event['accepted']
        group['acceptedPhysicalChange'] += event['accepted'] and not same_physical
        group['freshToOldArchive'] += event['archiveFresh']
        group['fallback'] += event['fallback']
        if not same_genes and same_physical and len(self.nuisance) < 4:
            self.nuisance.append({'paidFE': event['paidFE'], 'phase': event['phase'], 'parentId': parent['id'],
                                  'parentPositions': parent['positions'], 'childPositions': value['positions'],
                                  'objectives': value['objectives']})


def analyze(stem):
    folder = ENGINE/stem/'main'; catalog, = rows(folder/'catalog.jsonl'); receipt, = rows(folder/'receipt.jsonl')
    check = PhysicalReplay(catalog, receipt)
    handlers = {'initial': check.initial, 'model': check.model, 'step': check.step,
                'programEnd': check.program_end, 'generationEnd': check.generation_end}
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line); handlers[event['kind']](event)
    proof = check.finish()
    assert sum(g['paid'] for g in check.groups.values()) == receipt['successfulFE'] - 100
    return {'stem': stem, 'seed': catalog['seed'], 'firstTwoGenerationsOnly': True, 'paidReconstructionPassed': proof['passed'],
            'groups': {k: dict(v) for k, v in check.groups.items()}, 'nuisanceWitnesses': check.nuisance}


if __name__ == '__main__':
    result = {'instances': [analyze(stem) for stem in ('20_8_5_1', '100_2_3_1')],
              'scope': 'Posthoc descriptive accounting only. Not a causal explanation of the500k fresh-seed result or permission to retune the stopped two-phase version',
              'newSearchFE': 0, 'decoderCalls': 0, 'defaultMainlineChanged': False, 'goalAchieved': False}
    path = ENGINE/'physical-change-post-audit.json'; write_once(path, result)
    print(json.dumps({r['stem']: r['groups'] for r in result['instances']}, ensure_ascii=False))

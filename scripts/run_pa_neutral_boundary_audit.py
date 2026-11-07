"""Zero-FE reconstruction of strict specialist ties, before proposing any neutral relay change."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, rows, read, write_once, controller_lock
from pa_population_replay import Replay
from pa_population_state_checks import physical, snapshot
from research.semantic_repair.evidence import digest

SOURCE = ROOT/'runs/pa-population-engineering-20261105-164116-698339'


class NeutralAudit(Replay):
    def __init__(self, catalog):
        super().__init__(catalog); self.roles = {}; self.witnesses = []

    def mix(self, event):
        parent = self.population[event['slot']]; super().mix(event)
        role = event['role']; count = self.roles.setdefault(role, Counter()); count['paid'] += 1
        if role == 'CENTER':
            return
        target = {'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}[role]
        a, b = event['objectives'], parent['objectives']
        if a[target] < b[target]:
            count['ownImproved'] += 1
        elif a[target] > b[target]:
            count['ownWorsened'] += 1
        else:
            count['ownEqual'] += 1; assert not event['accepted']
            same = physical(event, self.catalog) == physical(parent, self.catalog)
            count['equalPhysicalSame'] += same
            if same:
                assert a == b
                return
            count['equalPhysicalChanged'] += 1
            weak_better = all(x <= y for x, y in zip(a, b)); weak_worse = all(y <= x for x, y in zip(a, b))
            kind = 'equalAllObjectives' if a == b else 'paretoImproved' if weak_better else 'paretoWorsened' if weak_worse else 'incomparable'
            count['equalPhysicalChanged.'+kind] += 1
            count['equalPhysicalChanged.freshArchive'] += event['archiveFresh']
            if kind == 'paretoImproved' and len(self.witnesses) < 8:
                self.witnesses.append({'paidFE': event['paidFE'], 'role': role, 'parentObjectives': b, 'childObjectives': a,
                                       'archiveFresh': event['archiveFresh'], 'subset': self.subsets[event['subset']]})


def analyze(stem):
    folder = SOURCE/stem/'main/audit'; catalog, = rows(folder/'catalog.jsonl'); receipt, = rows(folder/'receipt.jsonl')
    check = NeutralAudit(catalog['tuples'])
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            check.event(json.loads(line))
    assert receipt['status'] == 'COMPLETE' and receipt['successfulFE'] == check.paid == receipt['attemptedFE']
    assert receipt['paidSHA256'] == check.digest.hexdigest() and receipt['fees'] == dict(check.fees)
    assert receipt['completedGenerations'] == check.generations == 2 and receipt['completedPrograms'] == check.programs == 200
    for recorded, point in zip(receipt['lastPopulation'], check.population):
        snapshot(recorded, point)
    assert sorted(map(tuple, receipt['internalArchive'])) == sorted(map(tuple, check.archive))
    return {'stem': stem, 'frozenTrace': str(folder), 'successfulFEPreviouslyPaid': check.paid,
            'paidSequenceReconstructed': True, 'roles': {k: dict(v) for k, v in check.roles.items()}, 'witnesses': check.witnesses,
            'sourceHashes': {name: digest(folder/name) for name in ('events.jsonl', 'receipt.jsonl', 'catalog.jsonl')}}


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        assert read(SOURCE/'status.json')['engineeringPass']
        root = ROOT/'runs'/datetime.now().strftime('pa-neutral-boundary-audit-%Y%m%d-%H%M%S-%f'); root.mkdir()
        shutil.copy2(Path(__file__), root/Path(__file__).name)
        write_once(root/'protocol.json', {'version': 'STRICT_BOUNDARY_NEUTRAL_OBSERVATION-v1', 'source': str(SOURCE),
            'question': 'Which physically changed paid specialist candidates are rejected solely because their own scalar target is equal?',
            'scope': 'Descriptive existing two-generation traces. Not proof of the EQ500k cause, not a new algorithm or posthoc control promotion',
            'selection': 'All recorded steps, no choosing favorable seeds/masks/candidates', 'newSearchFE': 0, 'decoderCalls': 0,
            'defaultMainlineChanged': False, 'goalAchieved': False})
        print('PA_NEUTRAL_BOUNDARY_AUDIT_ROOT', root, flush=True)
        try:
            results = [analyze(stem) for stem in ('20_8_5_1', '100_2_3_1')]
            write_once(root/'analysis.json', {'instances': results, 'newSearchFE': 0, 'decoderCalls': 0, 'goalAchieved': False})
        except BaseException as error:
            write_once(root/'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'newSearchFE': 0, 'decoderCalls': 0}); raise
        write_once(root/'status.json', {'status': 'COMPLETE', 'newSearchFE': 0, 'decoderCalls': 0, 'goalAchieved': False})
        print('PA_NEUTRAL_BOUNDARY_AUDIT_COMPLETE', {r['stem']: r['roles'] for r in results}, flush=True)


if __name__ == '__main__':
    main()

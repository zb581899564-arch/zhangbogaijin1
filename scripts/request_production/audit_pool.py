"""Independent original pool, selector and experimental acceptance reconstruction."""
import numpy as np
from audit_inputs import RAW, FACTORY, ROLE, raw, require, same


def dominates(left, right):
    return all(a <= b for a, b in zip(left, right)) and any(a < b for a, b in zip(left, right))


def encoding(record):
    return tuple(tuple(record[key]) for key in ('jobs', 'machines', 'workers'))


class PoolLedger:
    """Independent finite nondominated pool; original strict comparisons and first ties."""
    def __init__(self, context):
        self.pools = [[] for _ in range(context['factories'])]
        self.accepted = self.rejected = self.truncated = self.observed = 0
        for f, records in enumerate(context['pools']):
            for record in records:
                self.offer(f, record)
            same(self.pools[f], records, 'Original retained pool changed during independent import')

    def offer(self, factory, candidate):
        pool = self.pools[factory]
        if any(encoding(r) == encoding(candidate) or dominates(r['objectives'], candidate['objectives']) for r in pool):
            self.rejected += 1
            return
        pool[:] = [r for r in pool if not dominates(candidate['objectives'], r['objectives'])]
        pool.append(candidate); self.accepted += 1
        if len(pool) > 8:
            self.truncated += 1
            self.truncate(pool)

    @staticmethod
    def truncate(pool):
        keep = []
        low = [min(r['objectives'][k] for r in pool) for k in range(3)]
        high = [max(0, max(r['objectives'][k] for r in pool)) for k in range(3)]
        for k in range(3):
            best = min(pool, key=lambda r: r['objectives'][k])
            if best not in keep:
                keep.append(best)
        def separation(record):
            def distance(chosen):
                total = 0.0
                for k in range(3):
                    delta = (record['objectives'][k]-chosen['objectives'][k])/max(1e-12, high[k]-low[k])
                    total += delta*delta
                return total
            return min(distance(chosen) for chosen in keep)
        while len(keep) < 8:
            keep.append(max((r for r in pool if r not in keep), key=separation))
        pool[:] = keep

    def observe(self, paid):
        for f in range(len(self.pools)):
            positions = [i for i, value in enumerate(paid['FA']) if value == f]
            record = {key: [paid[source][i] for i in positions]
                      for key, source in zip(('jobs', 'machines', 'workers'), ('JS', 'MA', 'WA'))}
            record.update(objectives=[paid[key][f] for key in FACTORY], paidFE=paid['fe'], stage='PROBE_PAID')
            self.offer(f, record)
        self.observed += 1

    def snapshot(self):
        return dict(factories=[dict(factory=f, records=records) for f, records in enumerate(self.pools)],
                    paidObservations=self.observed, accepted=self.accepted, rejected=self.rejected, truncated=self.truncated)

    def select(self, request):
        chosen = [min((r for r in pool if r['objectives'][0] <= request['cap']),
                      key=lambda r: weighted(r['objectives'], request), default=None) for pool in self.pools]
        possible = all(r is not None for r in chosen)
        predicted = ([max(r['objectives'][0] for r in chosen), sum(r['objectives'][1] for r in chosen),
                      sum(r['objectives'][2] for r in chosen)] if possible else None)
        return dict(chosen=chosen, feasible=possible, predicted=predicted)


def weighted(objectives, request):
    return objectives[1]/request['energyScale'] + request['eta']*objectives[2]/request['wageScale']


def decision(arm, role, child, parent, target, dominated):
    original = (all(a <= b for a, b in zip(child['objectives'], parent['objectives'])) or not dominated
                if role == 'CENTER' else child['objectives'][ROLE[role]] < parent['objectives'][ROLE[role]])
    def violation(point):
        return sum(max(value-target['cap'], 0)/target['cap'] for value in point['factoryMakespan'])
    cv, pv = violation(child), violation(parent)
    if arm == 'ROLE':
        keep, reason = original, 'ORIGINAL_ROLE'
    elif cv < pv:
        keep, reason = True, 'LOWER_VIOLATION'
    elif cv > pv:
        keep, reason = False, 'HIGHER_VIOLATION'
    elif arm == 'ORDINARY':
        keep, reason = weighted(child['objectives'], target) < weighted(parent['objectives'], target), 'EQUAL_VIOLATION_WEIGHTED'
    else:
        keep, reason = original, 'EQUAL_VIOLATION_ROLE'
    return dict(accepted=keep, originalRoleWouldAccept=original, acceptanceReason=reason,
                parentViolation=pv, candidateViolation=cv)


def check_assembly(assembly, paid, choice, context):
    same(assembly['performed'], True, 'Missing paid final assembly')
    same(assembly['fe'], 512, 'Final assembly charged at other than FE512')
    same(assembly['request'], context['actual'], 'Final selector used shuffled/effective rather than actual request')
    for key in ('chosen', 'feasible', 'predicted'):
        same(assembly[key], choice[key], 'Final original selector differs: ' + key)
    same(assembly['fallbackPaidParent'], not choice['feasible'], 'Assembly fallback changed')
    if choice['feasible']:
        expected = dict(JS=[], FA=[], MA=[], WA=[], objectives=choice['predicted'])
        for f, record in enumerate(choice['chosen']):
            for key, local in (('JS', 'jobs'), ('MA', 'machines'), ('WA', 'workers')):
                expected[key].extend(record[local])
            expected['FA'].extend([f]*len(record['jobs']))
        same({k: paid[k] for k in RAW[:4]}, {k: expected[k] for k in RAW[:4]}, 'Assembly does not concatenate chosen original local encodings')
        require(np.allclose(paid['objectives'], choice['predicted'], rtol=1e-9, atol=1e-10), 'Assembly chosen sum/max differs from paid objectives')
        duplicate = all(encoding(r) == tuple(tuple(context['parent'][key][i] for i, x in enumerate(context['parent']['FA']) if x == f)
                                             for key in ('JS', 'MA', 'WA')) for f, r in enumerate(choice['chosen']))
        same(assembly['duplicateParent'], duplicate, 'Duplicate-parent flag differs')
    else:
        same(raw(paid), context['parent'], 'Infeasible assembly must charge the exact target-parent fallback')
        same(assembly['duplicateParent'], False, 'Infeasible assembly duplicate flag differs')
    same(assembly['result'], raw(paid), 'Assembly receipt differs from paid row')

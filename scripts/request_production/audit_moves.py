"""Independent seeded neutral views, factory-block FOS and causal paid replay."""
from collections import Counter
import hashlib
import math
import numpy as np
from common import read
from audit_inputs import RAW, FACTORY, PROPOSAL, check_factory, check_raw, lines, raw, require, same
from audit_pool import PoolLedger, check_assembly, decision


def shuffle(rng, count):
    order = list(range(count))
    for size in range(count, 1, -1):
        other = rng.next_int(size)
        order[size-1], order[other] = order[other], order[size-1]
    return order


def initial_rng(context, before, models, seed, helpers):
    rng = helpers['JavaRandom'](seed)
    views = {r['slot']: r for r in before}
    expected_slots = [i for i, p in enumerate(context['points']) if p['family'] == context['actual']['family']]
    same([r['slot'] for r in before], expected_slots, 'Five receiver slots/order differ')
    same(models['slots'], expected_slots, 'Model slots differ')
    same(models['domain'], expected_slots, 'Model donor domain differs')
    same(Counter(r['role'] for r in before), Counter(MAKESPAN=1, CENTER=2, ENERGY=1, WORKER_COST=1), 'Role quota differs')
    for slot, point in enumerate(context['points']):
        keys = [None]*len(point['JS'])
        for f in range(context['factories']):
            jobs = [j for j, factory in zip(point['JS'], point['FA']) if factory == f]
            ordered = sorted((rng.next_bits(26)*(1 << 27)+rng.next_bits(27))/float(1 << 53) for _ in jobs)
            for job, key in zip(jobs, ordered):
                keys[job] = key
        if slot in views:
            view = views[slot]
            same(view['keys'], keys, 'Neutral keys differ from exact source-seeded Java RNG')
            same(helpers['physical'](view, context['factories']), helpers['physical'](point, context['factories']), 'Neutral view changed physical encoding')
            same(view['objectives'], point['objectives'], 'Neutral view changed objectives')
            same((view['stateId'], view['paidFE'], view['sourcePaidByFE'], view['role']),
                 (slot+1, -1, point['sourcePaidByFE'], point['role']), 'Initial state/source identity differs')
            check_raw(view, context); check_factory(view, context['factories'])
    orders = [shuffle(rng, len(models['masks'])) for _ in range(5)]
    same(models['initialOrders'], orders, 'Initial FOS shuffle differs')
    return rng, orders


def check_models(context, before, models):
    """Independent fixed-factory dependency formula and max average-linkage merges."""
    masks = models['masks']; expected_count = 2*len(context['fixed'])-context['factories']
    require(len(masks) == expected_count, 'Incomplete factory-block FOS')
    same(models['family'], context['actual']['family'], 'Model family changed')
    offset = 0
    for f in range(context['factories']):
        jobs = sorted(j for j, factory in context['fixed'].items() if factory == f)
        local = masks[offset:offset+2*len(jobs)-1]; offset += len(local)
        same(local[:len(jobs)], [[j] for j in jobs], 'Factory FOS singleton order differs')
        matrix = {}
        for a in jobs:
            for b in jobs:
                if a >= b:
                    continue
                p = sum(row['keys'][a] < row['keys'][b] for row in before)/5
                entropy = 0 if p in (0, 1) else -(p*math.log(p)+(1-p)*math.log(1-p))/math.log(2)
                matrix[a, b] = (1-entropy)*(1-sum((row['keys'][a]-row['keys'][b])**2 for row in before)/5)
        active = [[j] for j in jobs]
        for merged in local[len(jobs):]:
            same(merged, sorted(set(merged)), 'FOS merge is not a sorted job set')
            children = [group for group in active if set(group).issubset(merged)]
            require(len(children) == 2 and sorted(children[0]+children[1]) == merged, 'Invalid binary FOS merge')
            def average(a, b):
                return sum(matrix[tuple(sorted((x, y)))] for x in a for y in b)/(len(a)*len(b))
            selected = average(*children)
            maximum = max(average(a, b) for i, a in enumerate(active) for b in active[i+1:])
            require(abs(maximum-selected) < 3e-12, 'FOS merge fails independently recomputed average linkage')
            active = [group for group in active if group not in children] + [merged]
        same(active, [jobs], 'Factory FOS root omitted jobs')


def expected_proposal(fee, live, slots, models, rng, orders, context):
    receiver = (fee-1) % 5; count = (fee-1)//5
    round_no, step = divmod(count, len(models['masks']))
    if step == 0 and round_no:
        orders[receiver] = shuffle(rng, len(models['masks']))
    slot = slots[receiver]; donors = [value for value in slots if value != slot]
    donor_slot = donors[rng.next_int(4)]
    parent, donor = live[slot], live[donor_slot]
    subset = orders[receiver][step]
    return dict(receiver=receiver, slot=slot, role=parent['role'], round=round_no, step=step,
                subset=subset, donorSlot=donor_slot, mask=models['masks'][subset],
                parentId=parent['stateId'], donorId=donor['stateId'],
                parentPaidFE=parent['paidFE'], donorPaidFE=donor['paidFE'],
                parentSourcePaidByFE=context['points'][slot]['sourcePaidByFE'],
                donorSourcePaidByFE=context['points'][donor_slot]['sourcePaidByFE'])


def replay(folder, context, receipt, helpers):
    paid, steps = lines(folder/'paid.jsonl'), lines(folder/'steps.jsonl')
    before, after, models = read(folder/'before.json'), read(folder/'after.json'), read(folder/'models.json')
    require(len(before) == len(after) == 5, 'Expected five receiver states')
    rng, orders = initial_rng(context, before, models, receipt['seed'], helpers)
    check_models(context, before, models)
    catalog = helpers['collect_catalog'](before)
    for point in before:
        helpers['verify_encoding'](point, catalog, context['factories'])
    pool = PoolLedger(context); initial = pool.snapshot(); initial['initialSelection'] = pool.select(context['actual'])
    same(read(folder/'initial-pools.json'), initial, 'Initial pools, record order or chosen result differ')
    same(len(paid), receipt['successful'], 'Paid log count differs')
    same(receipt['paidLogRows'], len(paid), 'Paid evidence counter differs')
    same(len(steps), min(len(paid), 511), 'Production steps count differs')
    ledger = helpers['ParetoLedger'](context['background'])
    live = {r['slot']: r for r in before}; slots = list(live)
    counts = Counter(); per_slot = [0]*5; digest = hashlib.sha256()
    target = context['shuffled'] if receipt['arm'] == 'SHUFFLED' else context['actual']
    same(receipt['effectiveRequest'], target, 'Effective request treatment differs')
    for fe, point in enumerate(paid, 1):
        same(point['fe'], fe, 'Paid FE sequence is not contiguous')
        check_raw(point, context); check_factory(point, context['factories'])
        size = len(ledger.points); flags = ledger.offer(point['objectives'])
        expected_flags = dict(dominated=flags['dominated'], equal=flags['equal'], fresh=flags['admitted'],
                              archiveBefore=size, archiveAfter=len(ledger.points))
        for key, value in expected_flags.items():
            same(point[key], value, 'Independent pre-insertion archive flag differs: ' + key)
        helpers['update_paid_digest'](digest, point)
        if str(fe) in receipt['prefixSHA256']:
            same(receipt['prefixSHA256'][str(fe)], digest.hexdigest(), 'Paid prefix digest differs')
        if fe <= 511:
            same(point['stage'], 'PRODUCTION', 'Assembly charged before FE512')
            proposal = expected_proposal(fe, live, slots, models, rng, orders, context)
            same(point['producer'], proposal['role'], 'Paid producer role differs')
            step = steps[fe-1]
            for key in PROPOSAL:
                same(point[key], proposal[key], 'Paid proposal schedule/source differs: '+key)
                same(step[key], proposal[key], 'Step proposal schedule/source differs: '+key)
            same(raw(step), raw(point), 'Step genome/objectives differ from paid row')
            same(step['fe'], fe, 'Step fee differs')
            parent, donor = live[proposal['slot']], live[proposal['donorSlot']]
            helpers['verify_mix'](parent, donor, step, catalog, context['factories'])
            same(step['parentObjectives'], parent['objectives'], 'Step uses stale parent objectives')
            result = decision(receipt['arm'], proposal['role'], point, parent, target, flags['dominated'])
            for key, value in dict(result, **expected_flags).items():
                same(step[key], value, 'Independent acceptance/flags differ: '+key)
            same(step['candidateId'], 100+fe, 'Candidate state IDs skipped or repeated')
            counts[result['acceptanceReason']] += 1; counts['proposed.'+proposal['role']] += 1
            if result['accepted']:
                counts['accepted.'+proposal['role']] += 1
                live[proposal['slot']] = dict(step, **{k: point[k] for k in FACTORY},
                    stateId=100+fe, paidFE=fe, family=context['actual']['family'], sourcePaidByFE=parent['sourcePaidByFE'])
            if result['accepted'] != result['originalRoleWouldAccept']:
                counts['changedVersusOriginalRole'] += 1
            if result['candidateViolation'] == 0:
                counts['candidateFeasible'] += 1
            per_slot[proposal['receiver']] += 1
        else:
            same(point['stage'], 'ASSEMBLY', 'FE512 is not final composition')
            same(point['producer'], 'ORIGINAL_SHARED_SELECTOR', 'Assembly producer differs')
            check_assembly(read(folder/'assembly.json'), point, pool.select(context['actual']), context)
        pool.observe(point)
    same(receipt['paidSHA256'], digest.hexdigest(), 'Raw paid sequence SHA differs')
    same(receipt['acceptance'], dict(counts), 'Acceptance receipt counters differ')
    same(receipt['perReceiverFE'], per_slot, 'Five-slot round-robin counts differ')
    same(read(folder/'final-pools.json'), pool.snapshot(), 'Independent offer/truncation final pool differs')
    same(sorted(map(tuple, read(folder/'front.json'))), sorted(map(tuple, ledger.points)), 'Front is not exact ND(A0 + every paid candidate)')
    for result, slot in zip(after, slots):
        expected = live[slot]
        for key in RAW + FACTORY + ('resources', 'keys', 'stateId', 'paidFE', 'family', 'sourcePaidByFE', 'role'):
            same(result[key], expected[key], 'Final accepted working state differs: '+key)
    if receipt['failed']:
        proposal = expected_proposal(2, live, slots, models, rng, orders, context)
        same(receipt['pending'], dict(stage='PRODUCTION', **proposal), 'Failed second proposal pending evidence differs')
    else:
        same(receipt['pending'], None, 'Unexpected uncharged pending proposal')
    if len(paid) < 512:
        same(read(folder/'assembly.json'), {'performed': False}, 'Cutoff/failure constructed final composition')
    return dict(independentPaidRows=len(paid), independentProductionSteps=len(steps),
                factoryPoolOffers=len(paid)*context['factories'], independentFinalPool=True,
                independentAcceptance=True, exactSeededSchedule=True, independentAllPaidArchive=True)

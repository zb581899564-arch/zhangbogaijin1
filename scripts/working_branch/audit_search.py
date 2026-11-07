"""Replay accepted states and private archive flags from paid objectives, without a decoder."""
from collections import Counter
from audit_inputs import weak, dominates, keep
from common import *


def offer(archive, point):
    before = len(archive)
    dominated = any(dominates(a, point) for a in archive)
    equal = any(a == point for a in archive)
    result = archive if dominated or equal else [a for a in archive if not dominates(point, a)]+[point]
    return result, (dominated, equal, before, len(result))


def proposals(parent, donor, mask, catalog):
    resources, keys = parent['resources'][:], parent['keys'][:]
    for j in mask:
        resources[j], keys[j] = donor['resources'][j], donor['keys'][j]
    fallback = len({catalog[r][0] for r in resources}) != max(t[0] for t in catalog)+1
    if fallback:
        resources, keys = parent['resources'], parent['keys']
    return dict(resources=resources, keys=keys, **encode(resources, keys, catalog)), fallback


def program(c, arm, branch, tag, count, paid, endpoint, base, plan, donors, catalog):
    seed, initial = c[tag], paid[0]
    prefix = f"{c['id']}-{arm}-{branch}"
    assert len(paid) == count+1 and initial['id'] == prefix+'-INIT'
    archive, current = [a[:] for a in base], None
    for step, r in enumerate(paid, -1):
        assert (r['case'], r['context'], r['role'], r['arm'], r['branch'], r['step'], r['seedTag']) == (
            c['id'], c['context'], c['role'], arm, branch, step, tag)
        if step == -1:
            expected, fallback = seed, False
            assert r['isSeed'] and r['parentNumber'] == 0 and r['accepted'] is None
            assert r['objectives'] == seed['objectives']
            assert (r['node'], r['donorSlot'], r['maskJobs']) == (-1, -1, None)
        else:
            move = plan[branch][step]
            expected, fallback = proposals(current, donors[move['donorSlot']], move['mask'], catalog)
            assert r['id'] == prefix+'-'+str(step) and not r['isSeed']
            assert r['parentNumber'] == current['number']
            assert (r['node'], r['donorSlot'], r['maskJobs']) == (move['node'], move['donorSlot'], move['mask'])
        assert all(r[k] == expected[k] for k in (*FIELDS, 'resources', 'keys'))
        assert r['fallback'] == fallback
        archive, flags = offer(archive, r['objectives'])
        assert tuple(r[k] for k in ('archiveDominated', 'archiveEqual', 'archiveBefore', 'archiveAfter')) == flags
        accepted = current is None or keep(c['role'], r['objectives'], current['objectives'], flags[0])
        if step >= 0:
            assert r['accepted'] == accepted
        if accepted:
            current = r
    assert all(endpoint[k] == current[k] for k in (*FIELDS, 'resources', 'keys', 'objectives'))
    assert (endpoint['seedNumber'], endpoint['lastAcceptedNumber'], endpoint['lastAcceptedId'],
            endpoint['lastGeneratedNumber'], endpoint['programFE']) == (
            initial['number'], current['number'], current['id'], paid[-1]['number'], count+1)
    fresh = not any(weak(a, current['objectives']) for a in base)
    commit = keep(c['role'], current['objectives'], c['P']['objectives'], any(dominates(a, current['objectives']) for a in base))
    assert (endpoint['wouldCommit'], endpoint['freshToA0'], endpoint['fromSuccessor']) == (
        commit, fresh, current['number'] > initial['number'])


def verify(root):
    cases = read(root/'prepared/cases.json'); archives = read(root/'prepared/archives.json')
    _, entries, _, catalog = sources()
    plans = {c['id']: {b: [] for b in (0, 1)} for c in cases}
    for move in stream(root/'prepared/schedule.jsonl'):
        plans[move['case']][move['branch']].append(move)
    paid = rows(root/'science/evaluations.jsonl'); ends = rows(root/'science/endpoints.jsonl')
    assert len(paid) == 1536 and len(ends) == 84 and len({r['id'] for r in paid}) == 1536
    assert [r['number'] for r in paid] == list(range(1, 1537))
    pos = endpos = 0; cells = Counter(); seedcount = 0
    comparison = (*FIELDS, 'resources', 'keys', 'objectives', 'step', 'seedTag', 'isSeed', 'accepted',
                  'archiveDominated', 'archiveEqual', 'archiveBefore', 'archiveAfter', 'node', 'donorSlot', 'maskJobs', 'fallback', 'steps')
    for c in cases:
        donors = {p['slot']: p for p in entries[c['context']]['S'] if p['family'] == -1}
        prefixes = []
        for arm in ARMS:
            branch_tags = [(0, 'P', 31 if arm == 'ONE' else 15)]
            if arm != 'ONE':
                branch_tags.append((1, {'RESTART': 'P', 'CURRENT': 'R', 'BRANCH': 'Q'}[arm], 15))
            for branch, tag, count in branch_tags:
                chunk = paid[pos:pos+count+1]
                assert (ends[endpos]['case'], ends[endpos]['arm'], ends[endpos]['branch']) == (c['id'], arm, branch)
                program(c, arm, branch, tag, count, chunk, ends[endpos], archives[c['context']], plans[c['id']], donors, catalog)
                if branch == 0:
                    prefixes.append([{k: r[k] for k in comparison} for r in chunk[:16]])
                cells[c['context'], arm] += count+1; pos += count+1; endpos += 1; seedcount += 1
        assert prefixes[0] == prefixes[1] == prefixes[2] == prefixes[3]
    assert pos == 1536 and endpos == seedcount == 84 and all(v == 128 for v in cells.values()) and len(cells) == 12
    return dict(privatePrograms=84, paidSeedEvaluations=84, successorMixes=1452, pairedPrefixRows=12*4*16,
                privateArchiveAndEndpointReplay=True, armContextFE=128, newDecoderCalls=0)

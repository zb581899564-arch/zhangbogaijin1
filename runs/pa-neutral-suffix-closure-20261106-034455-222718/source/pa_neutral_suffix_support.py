"""Exact post-fork equivalence and extraction of the original receiver's natural remaining program."""
import hashlib
import json

from run_long_budget_bridge import rows
from pa_population_replay import Replay
from pa_population_state_checks import paid_bytes
from pa_neutral_replay import stored, mixed


def weak(a, b):
    return all(x <= y for x, y in zip(a, b))


def offer(archive, obj):
    dominated = any(weak(p, obj) and p != obj for p in archive)
    if dominated or obj in archive:
        return archive.copy(), dominated
    return [p for p in archive if not (weak(obj, p) and obj != p)]+[obj], dominated


def split_cases(folder):
    cases = json.loads((folder/'selected-cases.json').read_text('utf-8'))
    pairs = {p['case']: p for p in json.loads((folder/'pair-analysis.json').read_text('utf-8'))['pairs']}
    needed, pruned = [], []
    for case in cases:
        item = pairs[case['case']]; states, archives = [], []
        for branch, key in (('Actual', 'actualChild'), ('Rollback', 'rollbackChild')):
            point = dict(case[key], objectives=item[branch.lower()+'Objectives'])
            archive, dominated = offer(case['priorArchive'], point['objectives'])
            keep = weak(point['objectives'], case['receiver']['objectives']) or not dominated
            states.append(point if keep else case['receiver']); archives.append(archive)
        same = all(states[0][k] == states[1][k] for k in ('resources', 'keys', 'objectives')) and archives[0] == archives[1]
        if same:
            pruned.append({'case': case['case'], 'paidFE': case['paidFE'], 'exactWorkingAndArchiveEqual': True})
        else:
            needed.append(dict(case, rollbackChild=dict(case['rollbackChild'], objectives=item['rollbackObjectives'])))
    return needed, pruned


class SuffixExtraction(Replay):
    def __init__(self, catalog, needed):
        super().__init__(catalog, boundary_equal=True)
        self.wanted = {c['paidFE']: c for c in needed}; self.active = []; self.blocks = []

    def event(self, event):
        donor = stored(self.population[event['donorSlot']]) if event['kind'] == 'step' else None
        super().event(event)
        if event['kind'] == 'step':
            for block in self.active:
                assert event['generation'] == block['generation'] and event['slot'] == block['receiverSlot']
                block['moves'].append({'donor': donor, 'mask': self.subsets[event['subset']], 'expected': stored(event), 'rawPaidHash': event['rawPaidHash']})
            if event['paidFE'] in self.wanted:
                original = self.wanted[event['paidFE']]
                assert all(event[k] == original['actualChild'][k] for k in ('resources', 'keys', 'objectives'))
                block = dict(original, moves=[]); self.active.append(block); self.blocks.append(block)
        elif event['kind'] == 'programEnd':
            for block in self.active:
                block['expectedEndWorking'] = stored(self.population[event['slot']]); block['expectedEndArchive'] = self.archive.tolist()
            self.active = []


def extract(folder, needed):
    trace = folder/'EQUAL'; catalog, = rows(trace/'catalog.jsonl'); receipt, = rows(trace/'receipt.jsonl')
    check = SuffixExtraction(catalog['tuples'], needed)
    with (trace/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            check.event(json.loads(line))
    assert not check.active and len(check.blocks) == len(needed)
    assert check.digest.hexdigest() == receipt['paidSHA256'] and check.paid == receipt['successfulFE']
    return check.blocks, catalog


def write_program(folder, block, branch, catalog):
    folder.mkdir(parents=True)
    parent = block['receiver']; fork = block['actualChild'] if branch == 'ACTUAL' else block['rollbackChild']
    frames = [('PARENT', parent, [], parent, None), ('FORK', fork, [], fork, None)]
    frames += [('MOVE', m['donor'], m['mask'], m['expected'], m['rawPaidHash']) for m in block['moves']]
    with (folder/'program.tsv').open('x', encoding='utf-8') as stream:
        for kind, genes, mask, expected, raw in frames:
            raw = raw or hashlib.sha256(paid_bytes(expected, catalog, 0)).hexdigest()
            parts = [kind, ','.join(map(str, genes['resources'])), ','.join(repr(v) for v in genes['keys']),
                     ','.join(map(str, mask)) if mask else '-', ','.join(repr(v) for v in expected['objectives']), raw]
            stream.write('\t'.join(parts)+'\n')
    (folder/'prior-archive.tsv').write_text('\n'.join(','.join(repr(v) for v in p) for p in block['priorArchive'])+'\n', encoding='utf-8')
    return len(frames)


def validate_branch(folder, block, branch, catalog):
    receipt, = rows(folder/'receipt.jsonl'); points = rows(folder/'candidates.jsonl')
    assert receipt['status'] == 'COMPLETE' and receipt['failedFE'] == 0
    assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['paidFullTimelineQA'] == receipt['decoder']['dynamic.evaluations'] == len(points) == 2+len(block['moves'])
    working = None; archive = block['priorArchive']; expected_points = [block['receiver'], block['actualChild']]+[m['expected'] for m in block['moves']]
    for index, point in enumerate(points):
        if index == 0:
            genes = block['receiver']
        elif index == 1:
            genes = block['actualChild'] if branch == 'ACTUAL' else block['rollbackChild']
        else:
            move = block['moves'][index-2]; genes, _ = mixed(working, move['donor'], move['mask'], catalog)
        assert all(genes[k] == point[k] for k in ('resources', 'keys'))
        if branch == 'ACTUAL':
            assert all(point[k] == expected_points[index][k] for k in ('resources', 'keys', 'objectives'))
        new_archive, dominated = offer(archive, point['objectives'])
        keep = index == 0 or weak(point['objectives'], working['objectives']) or not dominated
        assert point['accepted'] == keep
        archive = new_archive
        if keep:
            working = point
    assert archive == receipt['internalArchive']
    assert working['resources'] == receipt['lastResources'] and working['keys'] == receipt['lastKeys'] and working['objectives'] == receipt['lastWorking']['objectives']
    if branch == 'ACTUAL':
        assert all(working[k] == block['expectedEndWorking'][k] for k in ('resources', 'keys', 'objectives'))
        assert archive == block['expectedEndArchive']
    return receipt

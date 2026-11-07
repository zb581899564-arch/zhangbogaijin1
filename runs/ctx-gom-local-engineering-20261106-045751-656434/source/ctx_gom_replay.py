"""Streaming proof of every paid archive notification and context-local view/model/proposal/acceptance."""
from collections import Counter, defaultdict
import hashlib
import json
import struct

import numpy as np

from run_long_budget_bridge import rows
from pa_population_state_checks import offer, physical, paid_bytes
from ctx_gom_model_checks import check as model_check


def raw_hash(raw):
    data = struct.pack('>q', 0)
    for key in ('JS','FA','MA','WA'):
        v = raw[key]; data += struct.pack('>i',len(v))+struct.pack('>'+'i'*len(v),*v)
    return hashlib.sha256(data+struct.pack('>ddd',*raw['objectives'])).hexdigest()


def snapshot(record, state):
    for key in ('id','paidFE','objectives'):
        assert record[key] == state[key], (key,record,state)


class Replay:
    def __init__(self, catalog):
        self.catalog = catalog; self.paid = {}; self.archive = np.empty((0,3)); self.states = {}
        self.population = []; self.families = []; self.sources = []; self.masks = defaultdict(list)
        self.passno = 0; self.program = None; self.pending = None; self.complete_passes = self.programs = self.local = self.views = 0
        self.visited = set(); self.models = []; self.physical_roles = Counter()

    def paid_event(self, e):
        assert e['fe'] == len(self.paid)+1
        flags = dict(objectives=e['objectives'],archiveDominated=e['dominated'],archiveEqual=e['equal'],archiveFresh=e['fresh'],
                     archiveSizeBefore=e['before'],archiveSizeAfter=e['after'])
        self.archive = offer(self.archive,flags); self.paid[e['fe']] = e

    def birth(self, e):
        assert e['id'] == len(self.states)+1 and e['objectives'] == self.paid[e['paidFE']]['objectives']
        self.states[e['id']] = e

    def view(self, e):
        if e['slot'] == 0:
            assert e['pass'] == self.passno+1
            self.passno += 1; self.population = []; self.families = []; self.sources = []; self.masks = defaultdict(list); self.visited = set()
        assert e['slot'] == len(self.population)
        self.birth(e); source = e['source']; assert raw_hash(source) == self.paid[e['paidFE']]['rawHash']
        assert source['objectives'] == e['objectives']
        byfa = lambda raw: tuple(tuple((j,m,w) for j,f,m,w in zip(raw['JS'],raw['FA'],raw['MA'],raw['WA']) if f == factory) for factory in range(self.catalog['factories']))
        assert physical(e,self.catalog['tuples']) == byfa(source)
        assert len(e['resources']) == len(e['keys']) == self.catalog['jobs'] and all(0 <= r < len(self.catalog['tuples']) for r in e['resources'])
        assert all(0 < k < 1 for k in e['keys'])
        self.population.append(e['id']); self.families.append(e['family']); self.sources.append(e); self.views += 1

    def model(self, e):
        assert e['pass'] == self.passno and len(self.population) == 100
        assert all(self.families[i] == e['family'] for i in e['slots'])
        assert e['slots'] == [i for i,f in enumerate(self.families) if f == e['family']]
        pop = {i:self.states[j] for i,j in enumerate(self.population)}
        # The free domain may have80members inside a100-slot workspace.
        result = model_check(e,pop,self.catalog); self.models.append(result); self.masks[e['family']].extend(e['subsets'])

    def ready(self, e):
        assert e['families'] == self.families and len(self.population) == 100
        counts = Counter(self.families)
        assert counts == Counter({-1:100}) or counts == Counter({-1:80,0:5,1:5,2:5,3:5})
        for family in counts:
            assert len(self.masks[family]) == (2*self.catalog['jobs']-1 if family < 0 else 2*self.catalog['jobs']-self.catalog['factories'])

    def start(self, e):
        assert self.program is None and e['pass'] == self.passno and e['slot'] not in self.visited
        family, slot = e['family'], e['slot']; assert family == self.families[slot]
        assert sorted(e['order']) == list(range(len(self.masks[family])))
        candidates = [i for i,s in enumerate(self.sources) if s['paidFE'] == e['inputFee'] and raw_hash(s['source']) == raw_hash(e['receiverRaw']) and i not in self.visited]
        assert candidates and slot == candidates[0]
        assert e['preference'] == 'CENTER' or e['preference'] == {1:'MAKESPAN',2:'CENTER',3:'ENERGY',4:'WORKER_COST'}[e['physicalGroup']]
        self.program = dict(e,nextStep=0); self.visited.add(slot)

    def proposal(self,e):
        p = self.program; assert p is not None and self.pending is None
        assert e['pass'] == self.passno and e['slot'] == p['slot'] and e['step'] == p['nextStep']
        assert e['subset'] == p['order'][e['step']]
        assert e['donorSlot'] != e['slot'] and self.families[e['donorSlot']] == p['family']
        parent, donor = self.states[self.population[e['slot']]],self.states[self.population[e['donorSlot']]]
        assert (e['parentId'],e['donorId']) == (parent['id'],donor['id'])
        resources, keys = parent['resources'].copy(),parent['keys'].copy()
        mask = self.masks[p['family']][e['subset']]
        for j in mask:
            resources[j],keys[j] = donor['resources'][j],donor['keys'][j]
        missing = len({self.catalog['tuples'][r][0] for r in resources}) != self.catalog['factories']
        assert e['fallback'] == missing
        if missing:
            resources,keys = parent['resources'].copy(),parent['keys'].copy()
        if p['family'] >= 0:
            assert not missing
            assert all(self.catalog['tuples'][a][0] == self.catalog['tuples'][b][0] for a,b in zip(resources,parent['resources']))
            assert len({self.catalog['tuples'][parent['resources'][j]][0] for j in mask}) == 1
        self.pending = dict(e,resources=resources,keys=keys,beforePaid=len(self.paid))

    def step(self,e):
        p = self.pending; assert p is not None
        for key in ('pass','slot','step','subset','donorSlot','parentId','donorId','fallback'):
            assert p[key] == e[key]
        assert e['paidFE'] == len(self.paid) == p['beforePaid']+1
        point = dict(e,resources=p['resources'],keys=p['keys']); self.birth(point)
        assert hashlib.sha256(paid_bytes(point,self.catalog['tuples'],0)).hexdigest() == self.paid[e['paidFE']]['rawHash']
        old = self.states[e['parentId']]['objectives']; target = {'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}.get(self.program['preference'])
        accept = (all(a<=b for a,b in zip(e['objectives'],old)) or not self.paid[e['paidFE']]['dominated']) if target is None else e['objectives'][target] < old[target]
        assert e['accepted'] == accept
        if accept:
            self.population[e['slot']] = e['id']
        self.program['nextStep'] += 1; self.local += 1; self.physical_roles[self.program['physicalGroup']] += 1; self.pending = None

    def end(self,e):
        assert self.pending is None and self.program['slot'] == e['slot'] and self.program['nextStep'] == len(self.program['order'])
        snapshot(e['result'],self.states[self.population[e['slot']]]); self.program = None; self.programs += 1

    def pass_end(self,e):
        assert len(self.visited) == 100 and self.program is None
        self.check_workspace(e['workspace']); self.complete_passes += 1

    def check_workspace(self,w):
        assert w['families'] == self.families and len(w['population']) == len(self.population)
        for actual,state_id in zip(w['population'],self.population):
            snapshot(actual,self.states[state_id])
        if self.pending is None:
            assert w['pending'] is None
        else:
            for key in ('pass','slot','step','subset','donorSlot','parentId','donorId','fallback'):
                assert w['pending'][key] == self.pending[key]


def replay(folder):
    catalog, = rows(folder/'catalog.jsonl'); receipt, = rows(folder/'receipt.jsonl'); r = Replay(catalog)
    handlers = {'paid':r.paid_event,'view':r.view,'model':r.model,'ready':r.ready,'program':r.start,
                'proposal':r.proposal,'step':r.step,'programEnd':r.end,'passEnd':r.pass_end}
    with (folder/'gom-events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            e = json.loads(line); handlers[e['kind']](e)
    assert receipt['status'] == 'COMPLETE' and receipt['error'] is None
    assert receipt['successful'] == receipt['paidFullTimelineQA'] == len(r.paid)
    assert receipt['attempted'] == receipt['successful']+receipt['failed'] and receipt['failed'] == receipt['timeInterruptedAttempts'] <= 1
    assert receipt['viewFullTimelineQA'] == r.views
    assert receipt['internalArchive'] == r.archive.tolist()
    assert {tuple(p['objectives']) for p in receipt['lastValidFront']} == set(map(tuple,r.archive))
    d = receipt['gom']; assert d['validatedViews'] == r.views and d['completePasses'] == r.complete_passes and d['completePrograms'] == r.programs and d['localEvaluations'] == r.local
    assert receipt['search'].get('jointLocal.evaluations',0) == r.local
    if d['workspace'] is not None:
        r.check_workspace(d['workspace'])
    else:
        assert not r.population
    if r.pending is not None:
        assert receipt['stopReason'] == 'TIME_LIMIT' and r.pending['beforePaid'] == receipt['successful']
    for p in rows(folder/'initial-population.jsonl'):
        assert raw_hash(p) == r.paid[p['fe']]['rawHash']
    return {'passed':True,'paidArchiveNotifications':len(r.paid),'views':r.views,'models':r.models,'localProposalsValidated':r.local,
            'completePasses':r.complete_passes,'completePrograms':r.programs,'physicalRoleLocalFE':dict(r.physical_roles),
            'retainedPendingProposal':r.pending is not None,'extraSearchFE':0,'decoderCalls':0}

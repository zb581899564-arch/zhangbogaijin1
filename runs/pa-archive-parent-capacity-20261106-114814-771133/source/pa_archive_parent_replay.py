"""Retain first paid physical carriers alongside the unchanged complete source replay."""
import hashlib
import json
from pathlib import Path

from run_long_budget_bridge import read,rows
from pa_regional_replay import RegionalReplay
from pa_population_state_checks import physical,snapshot
from pa_archive_parent_math import analyze_snapshot,summarize


def physical_hash(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode('utf-8')).hexdigest()


class ParentReplay(RegionalReplay):
    def __init__(self,catalog,mode,scale,events):
        super().__init__(catalog,mode,scale,events,[])
        self.carriers={};self.points={};self.seen_ids=set();self.snapshots=[]

    def record(self,point):
        fe=point['paidFE'];key=str(fe)
        if point['id'] in self.seen_ids:return fe
        self.seen_ids.add(point['id']);producer='INITIAL' if fe<=100 else point['role']
        value=dict(paidFE=fe,objectives=point['objectives'],producer=producer,
            strictSpecialistProduced=self.mode!='NO_SPECIALIST' and producer not in ('INITIAL','CENTER'),
            physicalHash=physical_hash(physical(point,self.catalog)))
        if key in self.points:assert self.points[key]==value
        else:self.points[key]=value
        return fe

    def paid_event(self,event):
        super().paid_event(event)
        if event['archiveFresh']:
            now=set(map(tuple,self.archive.tolist()))
            self.carriers={obj:point for obj,point in self.carriers.items() if obj in now}
            obj=tuple(event['objectives']);assert obj not in self.carriers
            point={k:(v.copy() if isinstance(v,list) else v) for k,v in event.items() if k in ('id','paidFE','role','resources','keys','objectives')}
            self.carriers[obj]=point;self.record(point)
        assert len(self.carriers)==len(self.archive)

    def capture(self,kind,generation,slots):
        assert set(self.carriers)==set(map(tuple,self.archive.tolist()))
        value=dict(kind=kind,generation=generation,asOfPaidFE=self.paid,parentSlots=slots,
            populationFE=[self.record(p) for p in self.population],archiveFE=[self.record(p) for p in self.carriers.values()])
        value['assessment']=analyze_snapshot(value,self.points);self.snapshots.append(value)
        if kind=='MODEL' and generation==1:assert value['assessment']['maximumMatches']==0

    def event(self,event):
        super().event(event)
        if event['kind']=='model':self.capture('MODEL',event['generation'],[i for i,p in enumerate(self.population) if p['role']=='CENTER'])

    def mix(self,event):
        if event['step']==0 and event['role']=='CENTER':
            assert event['paidFE']==self.paid+1
            self.capture('PROGRAM',event['generation'],[event['slot']])
        super().mix(event)


def analyze(spec,scale,plan):
    folder=Path(spec['source']);catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl')
    with (folder/'regional-events.jsonl').open(encoding='utf-8') as policy_stream:
        policy=(json.loads(line) for line in policy_stream);check=ParentReplay(catalog['tuples'],spec['mode'],scale,policy)
        with (folder/'events.jsonl').open(encoding='utf-8') as stream:
            for line in stream:check.event(json.loads(line))
        assert next(policy,None) is None
    assert receipt['successfulFE']==receipt['attemptedFE']==check.paid and receipt['paidSHA256']==check.digest.hexdigest()
    assert receipt['fees']==dict(check.fees) and check.programs==200 and check.generations==2 and receipt['failedFE']==0
    for saved,current in zip(receipt['lastPopulation'],check.population):snapshot(saved,current)
    assert sorted(map(tuple,receipt['internalArchive']))==sorted(check.carriers)==sorted(tuple(p['objectives']) for p in receipt['lastValidFront'])
    for point in receipt['lastValidFront']:
        chains=tuple(tuple((j,m,w) for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA']) if f==factory) for factory in range(catalog['factories']))
        first=check.carriers[tuple(point['objectives'])]
        assert physical_hash(chains)==check.points[str(first['paidFE'])]['physicalHash']
    return dict(instance=spec['instance'],mode=spec['mode'],primary=spec['primary'],paidRowsReplayed=check.paid,
        knownMixedGenomesRebuilt=check.paid-100,neutralViewsVerified=check.neutral,sourcePaidSHA256=check.digest.hexdigest(),
        exactSourceAcceptanceArchiveAndFirstExternalCarriersVerified=True,catalog=check.points,snapshots=check.snapshots,
        summary=summarize(check.snapshots,check.points,plan))

"""Independent live-genome/archive replay with fixed-region acceptance and paid ideals."""
from collections import Counter
import json
import numpy as np
from scipy.optimize import linear_sum_assignment

from run_long_budget_bridge import read,rows,write_once
from pa_population_replay import Replay
from pa_population_state_checks import snapshot


class RegionalReplay(Replay):
    def __init__(self,catalog,mode,scale,events,prefixes):
        super().__init__(catalog);self.mode=mode;self.scale=np.asarray(scale);self.policy_events=iter(events)
        self.ideal=np.full(3,np.inf);self.initial_points=[];self.weights=None;self.counts=Counter();self.saved_prefixes={};self.requested=set(prefixes)

    def paid_event(self,event):
        super().paid_event(event);self.ideal=np.minimum(self.ideal,event['objectives'])
        if self.paid in self.requested:self.saved_prefixes[str(self.paid)]=self.digest.copy().hexdigest()
        if event['kind']=='initial':
            self.initial_points.append(event['objectives'])
            if self.paid==100 and self.mode!='OFF':self.prepare_targets()

    def prepare_targets(self):
        weights=np.array([(a,b,c) for a in range(1,11) for b in range(1,11) for c in range(1,11) if a+b+c==12])
        points=np.asarray(self.initial_points);cost=(weights[None,:,:]*((points[15:70,None,:]-self.ideal)/self.scale)).max(axis=2)
        r,c=linear_sum_assignment(cost);self.weights={i+15:weights[int(col)] for i,col in enumerate(c)}
        event=next(self.policy_events);assert event['kind']=='targets' and event['mode']==self.mode and event['paidFE']==100
        assert event['columns']==c.tolist() and event['directions']==weights.tolist() and event['ideal']==self.ideal.tolist()
        assert abs(event['assignmentCost']-float(cost[r,c].sum()))<2e-12

    def decision(self,event,parent):
        a,b=event['objectives'],parent['objectives'];target={'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}.get(event['role'])
        center_native=all(x<=y for x,y in zip(a,b)) or not event['archiveDominated']
        native=center_native if target is None else a[target]<b[target]
        if self.mode=='OFF':return native
        old=new=None
        if target is None:
            w=self.weights[self.current_slot];old=float(np.max(w*((np.asarray(b)-self.ideal)/self.scale)))
            new=float(np.max(w*((np.asarray(a)-self.ideal)/self.scale)));keep=new<=old;self.counts['centerComparisons']+=1
        else:
            keep=center_native if self.mode=='NO_SPECIALIST' else native;self.counts['boundaryComparisons']+=1
        self.counts['nativeDecisionDifferences']+=keep!=native
        row=next(self.policy_events)
        assert row['kind']=='decision' and row['mode']==self.mode and row['paidFE']==self.paid
        assert row['slot']==self.current_slot and row['role']==event['role'] and row['parentId']==parent['id'] and row['childId']==event['id']
        assert row['ideal']==self.ideal.tolist() and row['nativeAccepted']==native and row['accepted']==keep
        for name,value in (('parentScore',old),('childScore',new)):
            assert row[name] is None if value is None else abs(row[name]-value)<2e-13
        return keep

    def mix(self,event):
        assert self.phase=='MIXING' and event['generation']==self.generation
        slot,donor_slot=event['slot'],event['donorSlot'];assert slot!=donor_slot and 0<=donor_slot<100
        if slot!=self.current_slot:
            assert slot==self.current_slot+1 and event['step']==0;self.current_slot=slot;self.used_subsets.clear()
        assert event['step']==len(self.used_subsets) and event['subset'] not in self.used_subsets
        self.used_subsets.add(event['subset']);subset=self.subsets[event['subset']]
        parent,donor=self.population[slot],self.population[donor_slot]
        assert event['parentId']==parent['id'] and event['parentHash']==parent['hash'] and event['parentObjectives']==parent['objectives']
        assert event['donorId']==donor['id'] and event['donorHash']==donor['hash'] and event['role']==parent['role']
        resources,keys=parent['resources'].copy(),parent['keys'].copy()
        for job in subset:resources[job],keys[job]=donor['resources'][job],donor['keys'][job]
        missing=len({self.catalog[r][0] for r in resources})!=max(t[0] for t in self.catalog)+1
        assert event['fallback']==missing
        if missing:resources,keys=parent['resources'],parent['keys']
        event.update(resources=resources,keys=keys)
        if missing:assert event['objectives']==parent['objectives']
        if len(subset)==len(resources):assert event['objectives']==donor['objectives']
        self.birth(event);self.paid_event(event);keep=self.decision(event,parent);assert event['accepted']==keep
        fresh=donor['id'] in self.accepted_ids;changed=donor['id'] in self.changed_ids
        assert event['donorAcceptedThisGeneration']==fresh and event['donorChangedThisGeneration']==changed
        self.fresh_reads+=fresh;self.changed_reads+=changed
        if keep:
            self.population[slot]=event;self.accepted_ids.add(event['id']);self.accepted+=1
            if event['hash']!=parent['hash']:self.changed_ids.add(event['id'])
        self.fallbacks+=missing;self.unchanged+=event['hash']==parent['hash'];self.fees['mixing']+=1


def replay(folder,mode,scale,prefixes):
    catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl')
    with (folder/'regional-events.jsonl').open(encoding='utf-8') as policy_stream:
        policy=(json.loads(line) for line in policy_stream);check=RegionalReplay(catalog['tuples'],mode,scale,policy,prefixes)
        with (folder/'events.jsonl').open(encoding='utf-8') as stream:
            for line in stream:check.event(json.loads(line))
        assert next(policy,None) is None
    assert receipt['successfulFE']==receipt['attemptedFE']==check.paid==receipt['paidFullTimelineQA'] and receipt['failedFE']==0
    assert check.digest.hexdigest()==receipt['paidSHA256'] and receipt['fees']==dict(check.fees) and check.neutral==receipt['reencodingFullTimelineQA']
    for key,value in (('accepted',check.accepted),('fallbacks',check.fallbacks),('unchangedStoredStates',check.unchanged),
        ('completeRawDuplicates',check.duplicates),('currentGenerationDonorReads',check.fresh_reads),('changedCurrentGenerationDonorReads',check.changed_reads),
        ('generation',check.generation),('completedGenerations',check.generations),('completedPrograms',check.programs),('phase',check.phase)):
        assert receipt[key]==value,(key,receipt[key],value)
    for saved,current in zip(receipt['lastPopulation'],check.population):snapshot(saved,current)
    expected=sorted(map(tuple,check.archive.tolist()))
    assert sorted(map(tuple,receipt['internalArchive']))==expected==sorted(tuple(p['objectives']) for p in receipt['lastValidFront'])
    policy=read(folder/'regional-policy.json')['policy'];assert policy['mode']==mode
    assert policy['observedPaid']==(0 if mode=='OFF' else check.paid) and policy['targetsReady']==(mode!='OFF' and check.paid>=100)
    for key in ('centerComparisons','boundaryComparisons','nativeDecisionDifferences'):assert policy[key]==check.counts[key]
    assert policy['ideal'] is None if mode=='OFF' else policy['ideal']==check.ideal.tolist()
    result=dict(passed=True,mode=mode,paidFE=check.paid,completedPrograms=check.programs,completedGenerations=check.generations,models=check.models,
        policyCounts=dict(check.counts),permanentTargetsAndAllPaidIdealsVerified=True,allMovesArchiveAcceptAndTimelineVerified=True,
        paidSHA256=check.digest.hexdigest(),prefixSHA256=check.saved_prefixes,newSearchFE=0,newDecoderCalls=0,performanceProved=False,goalAchieved=False)
    write_once(folder/'regional-independent-replay.json',result);return result

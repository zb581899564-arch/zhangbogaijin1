"""Independent role transition and noncontiguous receiver traversal, atop the complete PA trace."""
from collections import Counter
import hashlib
import json

from run_long_budget_bridge import read,rows,write_once
from pa_population_replay import Replay
from pa_population_state_checks import snapshot
from pa_role_semantics_data import expected
from qpa_geometry_audit_inputs import JavaRandom


class RoleReplay(Replay):
    def __init__(self,catalog,tasks,mode,seed):
        super().__init__(catalog);self.tasks=tasks;self.mode=mode;self.private=JavaRandom(seed)
        self.visit=[];self.visited=[];self.task_count=0;self.all_prefixes={}

    def paid_event(self,event):
        super().paid_event(event);self.all_prefixes[str(self.paid)]=self.digest.copy().hexdigest()

    def transition(self,generation):
        task=self.tasks[generation];assert task['generation']==generation and task['mode']==self.mode
        roles,visit=expected(self.population,self.mode,self.private)
        for slot,(old,before,after) in enumerate(zip(self.population,task['before'],task['after'])):
            for key in ('id','paidFE','role','hash','objectives','resources','keys'):assert before[key]==old[key]
            assert after['role']==roles[slot]
            for key in ('id','paidFE','hash','objectives','resources','keys'):assert after[key]==old[key]
            old['role']=roles[slot]
        assert task['visit']==visit and sorted(visit)==list(range(100))
        self.visit=visit;self.visited=[];self.task_count+=1

    def event(self,event):
        kind=event['kind']
        if kind=='reencode' and event['slot']==0:self.transition(event['generation'])
        if kind=='generationEnd':
            assert self.visited==self.visit and self.programs==self.generation*100
            for recorded,current in zip(event['population'],self.population):snapshot(recorded,current)
            self.generations+=1;self.phase='GENERATION_COMPLETE';return
        if kind=='step':self.mix(event);return
        super().event(event)

    def mix(self,event):
        assert self.phase=='MIXING' and event['generation']==self.generation
        slot,donor_slot=event['slot'],event['donorSlot'];assert slot!=donor_slot and 0<=donor_slot<100
        if slot!=self.current_slot:
            assert event['step']==0 and slot==self.visit[len(self.visited)] and slot not in self.visited
            self.visited.append(slot);self.current_slot=slot;self.used_subsets.clear()
        assert event['step']==len(self.used_subsets) and event['subset'] not in self.used_subsets
        self.used_subsets.add(event['subset']);subset=self.subsets[event['subset']]
        parent,donor=self.population[slot],self.population[donor_slot]
        assert event['parentId']==parent['id'] and event['parentHash']==parent['hash']
        assert event['donorId']==donor['id'] and event['donorHash']==donor['hash']
        assert event['parentObjectives']==parent['objectives'] and event['role']==parent['role']
        resources,keys=parent['resources'].copy(),parent['keys'].copy()
        for j in subset:resources[j],keys[j]=donor['resources'][j],donor['keys'][j]
        missing=len({self.catalog[r][0] for r in resources})!=max(t[0] for t in self.catalog)+1
        assert event['fallback']==missing
        if missing:resources,keys=parent['resources'],parent['keys']
        event.update(resources=resources,keys=keys)
        if missing:assert event['objectives']==parent['objectives']
        if len(subset)==len(resources):assert event['objectives']==donor['objectives']
        self.birth(event);self.paid_event(event)
        target={'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}.get(event['role']);obj,old=event['objectives'],parent['objectives']
        keep=(all(a<=b for a,b in zip(obj,old)) or not event['archiveDominated']) if target is None else obj[target]<old[target]
        assert event['accepted']==keep
        fresh=donor['id'] in self.accepted_ids;changed=donor['id'] in self.changed_ids
        assert event['donorAcceptedThisGeneration']==fresh and event['donorChangedThisGeneration']==changed
        self.fresh_reads+=fresh;self.changed_reads+=changed
        if keep:
            self.population[slot]=event;self.accepted_ids.add(event['id']);self.accepted+=1
            if event['hash']!=parent['hash']:self.changed_ids.add(event['id'])
        self.fallbacks+=missing;self.unchanged+=event['hash']==parent['hash'];self.fees['mixing']+=1


def replay(folder,mode,seed):
    catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl')
    tasks={e['generation']:e for e in rows(folder/'role-events.jsonl')};check=RoleReplay(catalog['tuples'],tasks,mode,seed)
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:check.event(json.loads(line))
    assert receipt['status']=='COMPLETE' and receipt['successfulFE']==receipt['attemptedFE']==check.paid==receipt['paidFullTimelineQA']
    assert receipt['failedFE']==0 and receipt['paidSHA256']==check.digest.hexdigest()
    assert receipt['reencodingFullTimelineQA']==check.neutral and receipt['fees']==dict(check.fees)
    for key,value in (('accepted',check.accepted),('fallbacks',check.fallbacks),('unchangedStoredStates',check.unchanged),
        ('completeRawDuplicates',check.duplicates),('currentGenerationDonorReads',check.fresh_reads),('changedCurrentGenerationDonorReads',check.changed_reads),
        ('generation',check.generation),('completedGenerations',check.generations),('completedPrograms',check.programs),('phase',check.phase)):
        assert receipt[key]==value,(key,receipt[key],value)
    for saved,current in zip(receipt['lastPopulation'],check.population):snapshot(saved,current)
    assert sorted(map(tuple,receipt['internalArchive']))==sorted(map(tuple,check.archive.tolist()))
    assert sorted(tuple(p['objectives']) for p in receipt['lastValidFront'])==sorted(map(tuple,check.archive.tolist()))
    assert check.task_count==len(tasks)
    result=dict(passed=True,mode=mode,paidFE=check.paid,roleTransitions=check.task_count,completePrograms=check.programs,
        completedGenerations=check.generations,models=check.models,allReceiverOrdersAndAcceptsVerified=True,paidSHA256=check.digest.hexdigest(),
        prefixSHA256=check.all_prefixes,newSearchFE=0,newDecoderCalls=0,performanceProved=False,goalAchieved=False)
    write_once(folder/'role-independent-replay.json',result);return result

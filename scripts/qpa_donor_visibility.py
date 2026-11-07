"""Streaming old-trajectory visibility audit; counterfactual proposals have no objective values."""
from collections import Counter,defaultdict
import hashlib
import json

from qpa_state_checks import child,identity,paid_bytes,model_check
from qgomea_reference_math import position_mix,order_mix
from qpa_physical_paid_audit import physical


def proposed(event,parent,donor,mask,catalog):
    resources=parent['resources'].copy()
    for job in mask:resources[job]=donor['resources'][job]
    if event['phase']==1:positions,_=position_mix(parent['positions'],donor['positions'],mask,event['reference'])
    else:positions=order_mix(parent['positions'],donor['positions'],mask)
    fallback=len({catalog['tuples'][r][0] for r in resources})!=catalog['factories']
    if fallback:resources,positions=parent['resources'].copy(),parent['positions'].copy()
    return dict(resources=resources,positions=positions),fallback


class Visibility:
    def __init__(self,catalog,receipt):
        self.catalog=catalog;self.receipt=receipt;self.population=[];self.parents=[];self.offspring=[];self.working=None
        self.paid=0;self.sha=hashlib.sha256();self.generation=0;self.completed=0;self.groups=defaultdict(Counter)
        self.witnesses=[];self.model_checks=[]

    def verify_paid(self,event,value):
        self.paid+=1;assert event['id']==event['paidFE']==self.paid and event['hash']==identity(value)
        raw=hashlib.sha256(paid_bytes(value,self.catalog['tuples'],0)).hexdigest();assert raw==event['rawPaidHash']
        self.sha.update(paid_bytes(value,self.catalog['tuples'],self.paid))

    def initial(self,event):
        assert event['slot']==len(self.population) and self.generation==0
        self.verify_paid(event,event);self.population.append(event)

    def model(self,event):
        assert len(self.population)==100 and self.generation==self.completed
        for actual,old in zip(event['parents'],self.population):assert actual['hash']==old['hash'] and actual['id']==old['id']
        self.parents=self.population[:];self.offspring=[];self.generation+=1;self.working=self.parents[0]
        self.active=event['activeSubsets']
        self.model_checks.append(model_check(event,{p['id']:p for p in self.parents},[p['id'] for p in self.parents]))

    def step(self,event):
        slot=event['slot'];donor_slot=event['donorSlot'];assert slot==len(self.offspring) and event['generation']==self.generation
        parent=self.working;donor=self.parents[donor_slot]
        assert event['parentId']==parent['id'] and event['donorId']==donor['id'] and event['donorHash']==donor['hash']
        value=child(event,parent,donor,self.active[event['subset']],self.catalog['tuples'],self.catalog['factories'])
        self.verify_paid(event,value);group=self.groups[str(self.generation)];group['paidMixingSteps']+=1
        if donor_slot<slot:
            latest=self.offspring[donor_slot];assert latest['paidFE']<event['paidFE'] and latest['role']==donor['role']
            group['completedDonorAvailable']+=1
            counterfactual,fallback=proposed(event,parent,latest,self.active[event['subset']],self.catalog)
            group['unscoredCompleteCounterfactualProposals']+=1
            raw_changed=counterfactual['resources']!=value['resources'] or counterfactual['positions']!=value['positions']
            changed=physical(counterfactual,self.catalog)!=physical(value,self.catalog)
            donor_changed=physical(latest,self.catalog)!=physical(donor,self.catalog)
            cross=parent['role']!=latest['role']
            group['freshDonorPhysicalChange']+=donor_changed;group['counterfactualRawChange']+=raw_changed
            group['counterfactualPhysicalChange']+=changed;group['counterfactualCrossRolePhysicalChange']+=cross and changed
            group['counterfactualSameRolePhysicalChange']+=not cross and changed
            group['fallbackChanged']+=fallback!=event['fallback']
            if changed and len(self.witnesses)<6:
                self.witnesses.append(dict(generation=self.generation,paidFE=event['paidFE'],slot=slot,donorSlot=donor_slot,
                    sourcePaidFE=latest['paidFE'],oldDonorId=donor['id'],availableDonorId=latest['id'],role=parent['role'],sourceRole=latest['role'],
                    phase=event['phase'],mask=self.active[event['subset']],unscoredCounterfactual=counterfactual))
        if event['accepted']:self.working=value

    def programEnd(self,event):
        assert event['slot']==len(self.offspring) and event['result']['hash']==self.working['hash']
        self.offspring.append(self.working)
        if len(self.offspring)<100:self.working=self.parents[len(self.offspring)]

    def generationEnd(self,event):
        assert len(self.offspring)==100
        assert [v['hash'] for v in event['population']]==[v['hash'] for v in self.offspring]
        self.population=self.offspring[:];self.completed+=1

    def finish(self):
        assert self.completed==self.generation==2 and self.paid==self.receipt['successfulFE']
        assert self.sha.hexdigest()==self.receipt['paidSHA256'] and self.receipt['failedFE']==0
        total=Counter()
        for group in self.groups.values():total.update(group)
        steps=total['paidMixingSteps'];changed=total['counterfactualPhysicalChange'];cross=total['counterfactualCrossRolePhysicalChange']
        return dict(successfulPaidHistoryReconstructed=self.paid,wholePaidSHA256=self.sha.hexdigest(),sourceGenerations=2,
            byGeneration={k:dict(v) for k,v in self.groups.items()},total=dict(total),physicalChangedFraction=changed/steps,
            crossRoleChangedFraction=cross/steps,coveragePass=changed/steps>=.2 and cross/steps>=.05,
            modelChecks=self.model_checks,unscoredWitnesses=self.witnesses,newSearchFE=0,newDecoderCalls=0)


def analyze(folder,catalog,receipt):
    observer=Visibility(catalog,receipt)
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line);getattr(observer,event['kind'])(event)
    return observer.finish()

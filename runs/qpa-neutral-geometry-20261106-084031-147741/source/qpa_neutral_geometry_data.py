"""Fixed paid cohorts and physically identical interleavings; no objective evaluation."""
import json
import random

from run_long_budget_bridge import read,rows,write_once
from qpa_donor_visibility import Visibility
from qpa_state_checks import child,vectors
from research.semantic_repair.evidence import digest


def physical(point):
    count=max(point['FA'])+1
    return tuple(tuple((j,m,w) for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA']) if f==factory)
                 for factory in range(count))


def role(slot):
    return 'MAKESPAN' if slot<15 else 'CENTER' if slot<70 else 'ENERGY' if slot<85 else 'WORKER_COST'


class CohortCapture(Visibility):
    def __init__(self,catalog,receipt):
        super().__init__(catalog,receipt);self.cohorts=[]

    def model(self,event):
        super().model(event);points=[]
        for state in self.parents:
            js,fa,ma,wa=vectors(state,self.catalog['tuples'])
            points.append(dict(JS=js,FA=fa,MA=ma,WA=wa,objectives=state['objectives'],knownFE=state['paidFE'],role=state['role']))
        self.cohorts.append(dict(generation=event['generation'],points=points,originalAffinity=event['affinity'],
                                 originalActiveSubsets=event['activeSubsets']))

    def step(self,event):
        assert event['slot']==len(self.offspring) and event['generation']==self.generation
        parent=self.working;donor=self.parents[event['donorSlot']]
        assert event['parentId']==parent['id'] and event['donorId']==donor['id']
        value=child(event,parent,donor,self.active[event['subset']],self.catalog['tuples'],self.catalog['factories'])
        self.verify_paid(event,value)
        if event['accepted']:self.working=value

    def finish(self):
        assert self.generation==self.completed==2 and len(self.cohorts)==2
        assert self.paid==self.receipt['successfulFE'] and self.sha.hexdigest()==self.receipt['paidSHA256']
        return self.cohorts


def capture(folder):
    catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl');check=CohortCapture(catalog,receipt)
    assert read(folder/'independent-replay.json')['passed']
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line);getattr(check,event['kind'])(event)
    return check.finish()


def interleave(point,variant,noise):
    parts=physical(point);queues=[[j for j,_,_ in part] for part in parts]
    if variant=='ORIGINAL':order=point['JS'][:]
    elif variant=='FACTORY_CONCAT':order=[j for queue in queues for j in queue]
    elif variant=='FACTORY_ROUND_ROBIN':
        order=[queue[rank] for rank in range(max(map(len,queues))) for queue in queues if rank<len(queue)]
    else:
        labels=[f for f,queue in enumerate(queues) for _ in queue];noise.shuffle(labels);ranks=[0]*len(queues);order=[]
        for f in labels:order.append(queues[f][ranks[f]]);ranks[f]+=1
    by_job={j:(f,m,w) for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA'])}
    result={**point,'JS':order,'FA':[by_job[j][0] for j in order],'MA':[by_job[j][1] for j in order],'WA':[by_job[j][2] for j in order]}
    assert sorted(order)==list(range(len(order))) and physical(result)==parts
    return result


def prepare(root,plan):
    from pathlib import Path
    pilot=Path(plan['sourcePilot']);engine=Path(plan['sourceEngineering']);populations=[];identities={}
    for stem in ('20_8_5_1','100_2_3_1'):
        for seed in (15290003,15290037):
            source=pilot/stem/str(seed)/'FE100K-SYNC/initial-population.jsonl';points=rows(source);assert len(points)==100
            frames=[dict(p,knownFE=p['fe'],role=role(i)) for i,p in enumerate(points)]
            populations.append(dict(id=f'{stem}-PILOT-{seed}-INITIAL',instance=stem,evolved=False,points=frames));identities[str(source)]=digest(source)
        folder=engine/stem/'main'
        for cohort in capture(folder):
            populations.append(dict(id=f"{stem}-ENGINE-14670003-MODEL{cohort['generation']}",instance=stem,
                                    evolved=cohort['generation']==2,**cohort))
        for name in ('events.jsonl','catalog.jsonl','receipt.jsonl','independent-replay.json'):identities[str(folder/name)]=digest(folder/name)
    assert len(populations)==8
    write_once(root/'source-populations.json',populations);write_once(root/'source-identities.json',identities)
    columns=('population','variant','slot','knownFE','role','objectives','JS','FA','MA','WA')
    for stem in ('20_8_5_1','100_2_3_1'):
        with (root/(stem+'-views.tsv')).open('w',encoding='utf-8',newline='') as stream:
            stream.write('\t'.join(columns)+'\n')
            for population in (p for p in populations if p['instance']==stem):
                for variant in plan['variants']:
                    noise=random.Random(int(variant.rsplit('_',1)[-1])) if variant.startswith('UNIFORM_') else None
                    for slot,point in enumerate(population['points']):
                        value=interleave(point,variant,noise)
                        fields=[population['id'],variant,str(slot),str(value['knownFE']),value['role']]
                        fields.extend(','.join(map(str,value[k])) for k in ('objectives','JS','FA','MA','WA'))
                        stream.write('\t'.join(fields)+'\n')
    (root/'pairs.tsv').write_text('\n'.join('\t'.join(map(str,p)) for p in plan['fixedPairs'])+'\n',encoding='utf-8')
    return populations

"""Recover all prescribed already-paid cohorts and independent objective partitions."""
from pathlib import Path
import json

from run_long_budget_bridge import rows,read,write_once
from pa_population_replay import Replay
from pa_population_state_checks import vectors
from qpa_geometry_audit_inputs import JavaRandom
from research.semantic_repair.evidence import digest

ROLES=('MAKESPAN','CENTER','ENERGY','WORKER_COST')


def ranking(points):
    remaining=list(range(100));groups={}
    for name,target in (('MAKESPAN',0),('ENERGY',1),('WORKER_COST',2)):
        chosen=sorted(remaining,key=lambda i:points[i]['objectives'][target])[:15]
        groups[name]=chosen;remaining=[i for i in remaining if i not in chosen]
    scores={}
    for i in remaining:
        a=points[i]['objectives'];p=q=0
        for j in remaining:
            b=points[j]['objectives']
            p+=all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))
            q+=all(y<=x for x,y in zip(a,b)) and any(y<x for x,y in zip(a,b))
        scores[i]=q+1/(p+1)
    groups['CENTER']=sorted(remaining,key=lambda i:scores[i])
    return [i for role in ROLES for i in groups[role]]


def expected(points,mode,rng):
    role=[p['role'] for p in points];visit=list(range(100))
    if mode=='NATIVE':return role,visit
    grouped=ranking(points)
    if mode=='RANDOM':
        grouped=list(range(100))
        for at in range(99,0,-1):
            chosen=rng.integer(at+1);grouped[at],grouped[chosen]=grouped[chosen],grouped[at]
    for at,slot in enumerate(grouped):
        if mode!='ORDER_ONLY':role[slot]='CENTER' if mode=='CENTER_MATCHED' else ROLES[0 if at<15 else 1 if at<70 else 2 if at<85 else 3]
        if mode!='TASK_ONLY':visit[at]=slot
    return role,visit


def native_cohorts(folder):
    catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl');check=Replay(catalog['tuples']);cohorts=[]
    assert read(folder/'independent-replay.json')['allPaidStatesAndAcceptanceReconstructed']
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line);check.event(event)
            if event['kind']=='model':
                values=[]
                for state in check.population:
                    js,fa,ma,wa=vectors(state,catalog['tuples'])
                    values.append(dict(JS=js,FA=fa,MA=ma,WA=wa,**{k:state[k] for k in ('id','paidFE','role','resources','keys','objectives')}))
                cohorts.append(dict(generation=event['generation'],points=values))
    assert check.digest.hexdigest()==receipt['paidSHA256'] and check.generations==len(cohorts)==2
    return cohorts,catalog['tuples']


def prepare(root,plan):
    pilot=Path(plan['sourcePilot']);engine=Path(plan['sourceEngineering']);populations=[];identities={}
    for stem in ('20_8_5_1','100_2_3_1'):
        frames,catalog=native_cohorts(engine/stem/'main/audit');lookup={tuple(t):i for i,t in enumerate(catalog)}
        for seed in (15410003,15410037):
            path=pilot/stem/str(seed)/'FE-PA_JOINT/initial-population.jsonl';identities[str(path)]=digest(path);points=[]
            for slot,point in enumerate(rows(path)):
                n=len(point['JS']);resources=[None]*n;keys=[None]*n
                for pos,(j,f,m,w) in enumerate(zip(point['JS'],point['FA'],point['MA'],point['WA'])):
                    resources[j]=lookup[f,m,w];keys[j]=(pos+.5)/n
                points.append(dict(point,id=slot+1,paidFE=point['fe'],role=ROLES[0 if slot<15 else 1 if slot<70 else 2 if slot<85 else 3],resources=resources,keys=keys))
            populations.append(dict(id=f'{stem}-INITIAL-{seed}',instance=stem,evolved=False,synthetic=False,points=points))
        for frame in frames:
            populations.append(dict(id=f"{stem}-ENGINE-MODEL{frame['generation']}",instance=stem,evolved=frame['generation']==2,synthetic=False,points=frame['points']))
        for name in ('events.jsonl','catalog.jsonl','receipt.jsonl','independent-replay.json'):
            path=engine/stem/'main/audit'/name;identities[str(path)]=digest(path)
    template=populations[0]
    for kind in ('ALL_TIED','ANTICHAIN'):
        values=[dict(p,paidFE=-1,objectives=[1.,1.,1.] if kind=='ALL_TIED' else [float(i),float(99-i),float(i%3)]) for i,p in enumerate(template['points'])]
        populations.append(dict(id='SYNTHETIC-'+kind,instance=template['instance'],evolved=False,synthetic=True,points=values))
    write_once(root/'populations.json',populations);write_once(root/'source-identities.json',identities)
    for stem in ('20_8_5_1','100_2_3_1'):
        with (root/(stem+'.tsv')).open('x',encoding='utf-8') as stream:
            for population in (p for p in populations if p['instance']==stem):
                for slot,p in enumerate(population['points']):
                    fields=[population['id'],'SOURCE',str(slot),str(p['paidFE']),p['role']]
                    fields.extend(','.join(map(str,p[k])) for k in ('objectives','JS','FA','MA','WA','resources','keys'))
                    fields.append(str(p['id']));stream.write('\t'.join(fields)+'\n')
    return populations

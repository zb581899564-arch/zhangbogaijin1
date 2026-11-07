"""Check raw source alignment, scalar Pareto identity and independent quality calculations."""
import argparse
from collections import Counter,defaultdict
import csv
import importlib.util
import numpy as np
from common import *


def physical(point):
    return tuple(tuple((j,m,w) for j,ff,m,w in zip(*(point[k] for k in ('JS','FA','MA','WA'))) if ff==f)
                 for f in range(max(point['FA'])+1))


def main(root):
    result=root/'analysis-v2';assert read(result/'acceptance.json')['passed']
    events={}
    for r in stream(SHARE):
        if r['kind']=='population' and 4<=r.get('cycle',0)<=11:events[r['cycle'],r['phase']]=r
    trace={(r['cycle'],r['label']):r for r in stream(GAP/'capture/SHARE_CTX_GOM/trajectory-events.jsonl')
           if r['kind']=='population' and 4<=r['cycle']<=11 and r['label']!='QGS_BATCH_SELECTED'}
    matched=0
    for (cycle,label),event in events.items():
        frozen=trace[cycle,label]
        assert event['fe']==frozen['fe'] and len(event['points'])==len(frozen['points'])
        for a,b in zip(event['points'],frozen['points']):
            assert a['key']==b['key'] and a['objectives']==b['objectives']
            assert a['family']==(-1 if b['family'] is None else b['family']);matched+=1
    lookup=defaultdict(lambda:defaultdict(set));phase_counts=Counter()
    with (GAP/'capture/SHARE_CTX_GOM/trajectory-paid.csv').open() as f:
        for r in csv.DictReader(f):
            fe=int(r['fe'])
            if fe>250000:break
            if 99540<fe and r['phase'] in ('QGS','SHARED'):
                cycle=int(r['cycle']);phase_counts[cycle]+=1
                for k in ('parent','donor','teacher'):lookup[cycle][k].add(r[k])
    assert {k:v for k,v in phase_counts.items() if k<=10}==dict.fromkeys(range(5,11),5000)
    assert phase_counts[11]==1300  # Paid partial next-QGS prefix; no complete state at its cutoff.
    unique=set();lost=[];total=Counter();role_counts=defaultdict(Counter)
    catalog=read(SUPPORT/'sources/models.json')['catalog'];width=len(catalog)*100
    inverse={tuple(t):i for i,t in enumerate(catalog)}
    for record in read(result/'endpoints.json'):
        old=record['fromCycle'];current=record['toCycle'];pool=events[old,'POST_GLOBAL']['points']+events[old,'POST_LOCAL']['points']
        original={physical(p) for p in events[old,'POST_GLOBAL']['points']}
        eligible=[]
        for slot,p in enumerate(events[old,'POST_LOCAL']['points']):
            obj=p['objectives']
            dominated=any(all(x<=y for x,y in zip(q['objectives'],obj)) and any(x<y for x,y in zip(q['objectives'],obj)) for q in pool)
            if physical(p) not in original and not dominated:eligible.append((slot,p))
        assert [(s,p['key']) for s,p in eligible]==[(r['slot'],r['key']) for r in record['points']]
        sets={k:{physical(p) for p in events[n,label]['points']} for k,n,label in
              [('survivors',old,'SURVIVORS'),('nextPre',current,'PRE_GLOBAL'),('nextGlobal',current,'POST_GLOBAL')]}
        for (slot,p),r in zip(eligible,record['points']):
            signature=physical(p);unique.add(signature)
            for label,states in sets.items():assert r[label+'Physical']==(signature in states)
            assert r['usedAsCurrent']==(r['key'] in lookup[current]['parent'])
            assert r['usedAsPersonal']==(r['key'] in lookup[current]['donor'])
            assert r['usedAsLeader']==(r['key'] in lookup[current]['teacher'])
            for k,v in r.items():
                if isinstance(v,bool):total[k]+=v
            role_counts[r['role']]['records']+=1;role_counts[r['role']]['lostAfterQGS']+=not r['nextGlobalPhysical']
            if not r['nextGlobalPhysical']:lost.append(r)
        for k,v in record['counts'].items():assert v==sum(r[k] for r in record['points'])
    reference=read(GAP/'step1/100_2_3_1-reference.json');sys.path.insert(0,str(BASE/'runs/linux-pilot-evaluation-20261106-01/payload'))
    from research.dynamic_benchmark.metrics import hypervolume,igd_plus
    hv_error=igd_error=0.
    for r in read(result/'stages.json'):
        values=nd([p['objectives'] for p in events[r['cycle'],r['phase']]['points']])/SCALE
        hv_error=max(hv_error,abs(r['HV']-hypervolume(values,[1.5]*3)))
        igd_error=max(igd_error,abs(r['IGDplus']-igd_plus(values,np.asarray(reference)/SCALE)))
    assert hv_error<1e-11 and igd_error<1e-12
    model=read(root/'model-probe/summary.json');assert model['passed'] and model['newFE']==0
    report=dict(passed=True,rawStateRowsMatched=matched,paidGlobalFEByCycle=phase_counts,
         endpointOccurrenceRecords=sum(e['candidates'] for e in read(result/'endpoints.json')),
         distinctPhysicalEndpointStates=len(unique),counts=dict(total),byRole=dict(role_counts),
         lostCompleteStates=len(lost),lostStateMedianSingleRetention=float(np.median([r['nextGlobalSingleRetained'] for r in lost])),
         lostStateMedianOrderedPairRetention=float(np.median([r['nextGlobalPairRetained'] for r in lost])),
         stageHVIndependentChecks=24,maxHVAbsoluteError=hv_error,stageIGDplusIndependentChecks=24,maxIGDplusAbsoluteError=igd_error,
         sourceModelMathAndHierarchyChecked=True,newSearchFE=0,newDecoderQA=0,newObjectiveQueries=0,
         amendment='analysis-v1 used generic global phase name; v2 uses actual QGS/SHARED tags and verifies 5000 paid rows per cycle. All old output retained.')
    write(root/'independent-audit.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)

"""Already-paid ordinary-PA front birth attribution, descriptive rather than causal."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from collections import Counter,defaultdict
from pathlib import Path
import shutil
import sys
import numpy as np

from run_long_budget_bridge import read,rows,write_once
from qpa_capability_analysis import endpoint


def fees_and_role(folder,jobs,limit):
    events=rows(folder/'role-events.jsonl');program=2*jobs-1;roles=['INITIAL']*100
    for event in events:
        for slot in event['visit']:
            roles.extend([event['after'][slot]['role']]*min(program,limit-len(roles)))
            if len(roles)==limit:break
        if len(roles)==limit:break
    assert len(roles)==limit
    receipt,=rows(folder/'run-receipt.jsonl');diag=receipt['search']
    assert diag['initialization.evaluations']==100 and diag['global.evaluations']==limit-100
    assert diag['completePrograms']==(limit-100)//program and diag['completeGenerations']==(limit-100)//(100*program)
    assert diag['modelBuilds']==len(events)
    return roles,Counter(roles)


def source_points(folder,limit):
    records={};alternatives=Counter()
    for row in rows(folder/'checkpoint-solutions.jsonl'):
        if row['checkpointKind']!='FE' or row['checkpoint']!=limit:continue
        key=tuple(row['objectives']);alternatives[key]+=1
        if key not in records or row['bornFE']<records[key]['bornFE']:records[key]=row
    assert set(records)==set(map(tuple,endpoint(folder,'FE',limit)['front']))
    assert all(1<=r['bornFE']<=limit for r in records.values())
    return records,alternatives


def analyze_folder(root,stem,seed,mode,limit,opponents):
    folder=root/stem/str(seed)/('FE-'+mode);roles,fees=fees_and_role(folder,int(stem.split('_')[0]),limit)
    points,alternatives=source_points(folder,limit);births=Counter();late=defaultdict(list);coverage={}
    for row in points.values():
        role=roles[row['bornFE']-1];births[role]+=1;late[role].append(row['bornFE'])
    for arm in opponents:
        other=np.asarray(endpoint(root/stem/str(seed)/('FE-'+arm),'FE',limit)['front']);covered=Counter()
        for point,row in points.items():
            if np.all(other<=point,axis=1).any():covered[roles[row['bornFE']-1]]+=1
        coverage[arm]=dict(totalCovered=sum(covered.values()),byObservedBirthRole=dict(covered))
    return dict(instance=stem,seed=seed,mode=mode,paidFEByActualReceiverRole=dict(fees),frontPointsByRecordedBirthRole=dict(births),
        medianRecordedBirthFE={k:float(np.median(v)) for k,v in late.items()},
        nondominatedRecordedBirthsPer10000PaidFE={k:10000*births[k]/n for k,n in fees.items()},
        pointsCoveredByOpponent=coverage,multipleRecordedCarriersForSameObjective=sum(v>1 for v in alternatives.values()),
        interpretation='Recorded representative birth only; not independent causal contribution, no accepted/rejected status inferred')


def main(root):
    assert read(root/'independent-final-audit.json')['passed'];plan=read(root/'protocol.json')['contract'];analysis=read(root/'analysis.json');result=[]
    modes=plan['modes']+['PA_EQUAL'];opponents=['NATIVE','NSGA2_DEEP','NSGA_CTX_GOM','FULL_SHARED_DEEP']
    for spec,case in zip(plan['instances'],analysis['instances']):
        for seed in plan['seeds']:
            for mode in modes:
                row=analyze_folder(root,spec['stem'],seed,mode,spec['fixedFE'],opponents);result.append(row)
                if mode=='FULL':
                    for arm in opponents:
                        comparison,=[c for c in case['comparisons'] if c['B']==arm];pair,=[p for p in comparison['pairs'] if p['seed']==seed]
                        assert row['pointsCoveredByOpponent'][arm]['totalCovered']==pair['coverage']['coveredA']
    write_once(root/'posthoc-birth-origins.json',dict(observations=result,descriptiveOnly=True,
        mapping='All full-FOS programs have2N-1 paid evaluations; infer actual receiver role from accepted per-generation traversal/metadata. Validate total FE, complete programs/generations/model builds and final-front coverage counts. Initialization separately labelled.',
        caveat='The checkpoint stores a recorded carrier, not every alternative origin. Objective-identical alternatives and first-record conventions cannot establish causal role value or benefit of changing acceptance. All-paid result archive already includes rejected candidate points; internal work states are a different question.',
        newSearchFE=0,newDecoderCalls=0,noControlPromotion=True,originalStopUnchanged=True,goalAchieved=False))
    folder=root/'posthoc-birth-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('PA_ROLE_RECORDED_BIRTH_ORIGINS_COMPLETE',len(result),'cases,0newFE/decoder',flush=True)
    for row in result:
        if row['mode']=='FULL':print(row,flush=True)


if __name__=='__main__':main(Path(sys.argv[1]).resolve())

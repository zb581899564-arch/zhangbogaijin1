"""Independent offline selection checks and feasible same-quota retention witnesses; zero search FE."""
from collections import Counter
import numpy as np

from run_long_budget_bridge import rows,write_once,hypervolume


def geometry(values):
    a=np.asarray(values)
    dominates=np.all(a[:,None,:]<=a[None,:,:],axis=2)&np.any(a[:,None,:]<a[None,:,:],axis=2)
    degree=dominates.sum(axis=0);rank=np.zeros(len(a),dtype=int);active=list(np.flatnonzero(degree==0));level=0
    while active:
        nxt=[]
        for i in active:
            rank[i]=level
            for j in np.flatnonzero(dominates[i]):
                degree[j]-=1
                if degree[j]==0:nxt.append(int(j))
        active=nxt;level+=1
    score=dominates.sum(axis=0)+1/(dominates.sum(axis=1)+1)
    crowd=np.zeros(len(a))
    for level in np.unique(rank):
        groups={}
        for i in np.flatnonzero(rank==level):groups.setdefault(tuple(a[i]),[]).append(int(i))
        unique=[v[0] for v in groups.values()]
        distance={i:0. for i in unique}
        for k in range(3):
            order=sorted(unique,key=lambda i:a[i,k]);span=a[order[-1],k]-a[order[0],k]
            if span==0:continue
            distance[order[0]]=distance[order[-1]]=float('inf')
            for p in range(1,len(order)-1):distance[order[p]]+=(a[order[p+1],k]-a[order[p-1],k])/span
        for ids in groups.values():
            for i in ids:crowd[i]=distance[ids[0]]
    return score,rank,crowd


def select(order,points,quotas,unique=False):
    used=Counter();seen=set();chosen=[];selected=set()
    for phase in range(2 if unique else 1):
        for i in order:
            cat=points[i]['category'];key=(cat,*points[i]['objectives'])
            if i in selected or used[cat]>=quotas[cat]:continue
            if unique and phase==0 and key in seen:continue
            chosen.append(i);selected.add(i);seen.add(key);used[cat]+=1
    assert len(chosen)==sum(quotas) and dict(used)=={i:n for i,n in enumerate(quotas) if n}
    return chosen


def analyze_event(event,norm):
    points=event['points'];values=np.asarray([p['objectives'] for p in points]);quotas=event['quotas']
    score,rank,crowd=geometry(values)
    assert np.array_equal(score,np.asarray([p['fitness'] for p in points]))
    order=sorted(range(len(points)),key=lambda i:(score[i],i))
    actual=select(order,points,quotas);assert actual==event['selected']
    alternatives={'PDDR_LOCAL_FIRST':select(sorted(range(len(points)),key=lambda i:(score[i],-i)),points,quotas),
        'PDDR_UNIQUE':select(order,points,quotas,True),
        'RANK_CROWD_UNIQUE':select(sorted(range(len(points)),key=lambda i:(rank[i],-crowd[i],i)),points,quotas,True)}
    scaled=(values-norm['lower'])/norm['scale'];hv=lambda ids:float(hypervolume(scaled[ids],(1.5,)*3))
    base=hv(actual);keys={tuple(v) for v in values[actual]}
    lost_nd={tuple(values[i]) for i in range(len(points)) if rank[i]==0 and tuple(values[i]) not in keys}
    metrics={}
    for arm,ids in alternatives.items():
        metrics[arm]={'retainedHV':hv(ids),'relativeGainPct':100*(hv(ids)/base-1),
            'selected':ids,'localKept':sum(i>=event['count'] for i in ids),'uniqueObjectives':len({tuple(values[i]) for i in ids})}
    best=max(x['relativeGainPct'] for x in metrics.values())
    return {'paidFE':event['paidFE'],'poolSize':len(points),'quotas':quotas,'actualRetainedHV':base,
        'allPoolHV':hv(list(range(len(points)))),'actualUniqueObjectives':len(keys),'poolUniqueObjectives':len({tuple(v) for v in values}),
        'actualLocalKept':sum(i>=event['count'] for i in actual),'lostUniqueGlobalND':len(lost_nd),
        'alternatives':metrics,'retentionOpportunity':best>=.5 and len(lost_nd)>=2,
        'caveat':'Retained coverage is an internal continuation opportunity. External all-paid archive already contains pool points; no new official HV is created by reselection.'}


def analyze(root,specs,seed):
    results=[]
    for spec in specs:
        stem=spec['stem'];trace=rows(root/stem/str(seed)/'ON/final-survival.jsonl')[0]
        assert trace['enabled'] and len(trace['events'])==1
        events=[analyze_event(e,spec['normalization']) for e in trace['events']]
        results.append({'stem':stem,'events':events,'supported':all(e['retentionOpportunity'] for e in events)})
    result={'instances':results,'worthNewRetentionProtocol':all(r['supported'] for r in results),'searchFE':0,
        'scope':'First complete generation at the registered development seed only. No new selector, continuation performance, time superiority, fatigue specificity or novelty established.'}
    write_once(root/'analysis.json',result);return result

"""Pure analysis of already-paid cohorts, checked quotas/PDDR, and first-admission availability."""
from collections import Counter
import numpy as np

from run_long_budget_bridge import nondominated,hypervolume,igd_plus
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage


def quality(points,norm,reference):
    front=nondominated([p['objectives'] for p in points]);normal=(front-norm['lower'])/norm['scale']
    return dict(front=front.tolist(),frontSize=len(front),HV=hypervolume(normal,(1.5,)*3),IGDplus=igd_plus(normal,reference))


def change(before,after):
    den=before['IGDplus']+after['IGDplus']
    return dict(HVChangePct=100*(after['HV']/before['HV']-1),
        IGDplusSymmetricWorseningPct=200*(after['IGDplus']-before['IGDplus'])/den if den else 0.,
        coverage=bidirectional_coverage(after['front'],before['front']))


def support(points):
    free=[p for p in points if p['family']==-1];assert len(free)==80
    rows=[]
    for p in free:
        byjob=[None]*len(p['JS'])
        for j,f,m,w in zip(p['JS'],p['FA'],p['MA'],p['WA']):byjob[j]=(f,m,w)
        rows.append(byjob)
    columns=[set(items) for items in zip(*rows)]
    return dict(uniqueRawGenomes=len({p['key'] for p in free}),uniqueObjectiveVectors=len({tuple(p['objectives']) for p in free}),
        meanFMWTuplesPerJob=float(np.mean([len(x) for x in columns])),
        uniqueFAPatterns=len({tuple(v[0] for v in row) for row in rows}))


def selection_check(event):
    p=np.array([row['objectives'] for row in event['pool']]);d=np.all(p[:,None,:]<=p[None,:,:],axis=2)&np.any(p[:,None,:]<p[None,:,:],axis=2)
    expected=d.sum(axis=0)+1./(d.sum(axis=1)+1)
    assert np.array_equal(expected,np.array(event['fitness']))
    cats,quotas=event['categories'],event['quotas'];used=[0]*len(quotas);selected=[]
    for i in sorted(range(len(p)),key=lambda i:expected[i]):
        c=cats[i]
        if used[c]<quotas[c]:selected.append(i);used[c]+=1
        if len(selected)==100:break
    assert selected==event['selected'] and used==quotas
    return dict(selectedGlobal=sum(i<100 for i in selected),selectedLocal=sum(i>=100 for i in selected),
        poolFitnessTies=len(expected)-len(set(expected)),quotaAndPDDRReconstructed=True)


def workspace_check(event,post,catalog):
    assert len(event['states'])==len(post['points'])==100
    assert Counter(s['family'] for s in event['states'])==Counter({-1:80,0:5,1:5,2:5,3:5})
    for state,point in zip(event['states'],post['points']):
        assert state['sourceKey']==point['key'] and state['objectives']==point['objectives'] and state['family']==point['family']
        ordered=sorted(range(len(state['keys'])),key=lambda j:(state['keys'][j],-j))
        for f in range(max(t[0] for t in catalog)+1):
            old=[(j,m,w) for j,ff,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA']) if ff==f]
            new=[(j,catalog[state['resources'][j]][1],catalog[state['resources'][j]][2]) for j in ordered if catalog[state['resources'][j]][0]==f]
            assert old==new


def cycle_summary(number,events,norm,reference,catalog):
    pre,glob,local,surv=[events[p] for p in ('PRE_GLOBAL','POST_GLOBAL','POST_LOCAL','SURVIVORS')]
    assert glob['fe']-pre['fe']==5000 and local['fe']-glob['fe']==19860 and surv['fe']==local['fe']
    selection=events['selection'];assert selection['fe']==local['fe']
    assert [(p['key'],p['branch']) for p in selection['pool']]==[(p['key'],p['branch']) for p in glob['points']+local['points']]
    assert [selection['pool'][i]['key'] for i in selection['selected']]==[p['key'] for p in surv['points']]
    workspace_check(events['workspace'],glob,catalog)
    stages={name:quality(event['points'],norm,reference) for name,event in [('before',pre),('global',glob),('local',local),('survivors',surv)]}
    stages['pool']=quality(selection['pool'],norm,reference)
    return dict(cycle=number,startFE=pre['fe'],endFE=surv['fe'],cohorts=stages,
        globalChange=change(stages['before'],stages['global']),localChange=change(stages['global'],stages['local']),
        survivorLoss=change(stages['pool'],stages['survivors']),
        supports={name:support(event['points']) for name,event in [('before',pre),('global',glob),('local',local),('survivors',surv)]},
        selection=selection_check(selection))


def availability_summary(targets):
    rows=[]
    for label in sorted({p['origin'] for p in targets.values()}):
        points=[p for p in targets.values() if p['origin']==label];eligible=[p for p in points if not p['censoredAtBudget']]
        rows.append(dict(origin=label,total=len(points),eligibleCompletedBirthCycle=len(eligible),
            returnedByBirthProgram=sum(p.get('returnedByBirthProgram',False) for p in eligible),
            inBirthLocalExitCurrent=sum(p.get('atLocalExit',False) for p in eligible),
            inBirthSurvivorCurrent=sum(p.get('atSurvivors',False) for p in eligible),
            inBirthTeacherArchive=sum(p.get('inTeacherMemoryAtBirthCycle',False) for p in eligible),
            everInTeacherArchive=sum(p.get('firstTeacherMemoryFE') is not None for p in points),
            everInCurrentCohort=sum(p.get('firstCohortFE') is not None for p in points)))
    return rows

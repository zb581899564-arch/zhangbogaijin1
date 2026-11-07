"""Trace full paid states and structural fragments through complete cycles 5--10, at zero FE."""
import argparse
from collections import Counter,defaultdict
import csv
import time
import numpy as np
from common import *
from structure import describe,feature_sets,retention,cohort,pair_motion,json_safe


def load_cycles(catalog):
    cycles=defaultdict(dict)
    for e in stream(SHARE):
        if not 4<=e.get('cycle',0)<=11:continue
        if e['kind']=='population':
            for p in e['points']:describe(p,catalog)
            cycles[e['cycle']][e['phase']]=e
        elif e['kind']=='selection':cycles[e['cycle']]['selection']=e
        elif e['kind']=='workspace':cycles[e['cycle']]['workspace']=e
    for n in range(4,11):
        c=cycles[n];g,l,s=[c[k] for k in ('POST_GLOBAL','POST_LOCAL','SURVIVORS')]
        assert l['fe']-g['fe']==19860 and s['fe']==l['fe']
        pool=g['points']+l['points'];selection=c['selection']
        assert [(p['key'],p['branch']) for p in pool]==[(p['key'],p['branch']) for p in selection['pool']]
        assert [(pool[i]['key'],pool[i]['branch']) for i in selection['selected']]==[(p['key'],p['branch']) for p in s['points']]
        assert Counter(p['_physical'] for p in s['points'])==Counter(p['_physical'] for p in cycles[n+1]['PRE_GLOBAL']['points'])
    return cycles


def trace_paid(keys):
    uses=defaultdict(lambda:defaultdict(set))
    path=GAP/'capture/SHARE_CTX_GOM/trajectory-paid.csv'
    with path.open() as f:
        for row in csv.DictReader(f):
            fe=int(row['fe'])
            if fe>250000:break
            if row['phase'] not in ('QGS','SHARED') or fe<=99540:continue
            for field in ('parent','donor','teacher'):
                if row[field] in keys:
                    uses[int(row['cycle'])][field].add(row[field])
    return uses


def eligible_local(cycle):
    before,after=cycle['POST_GLOBAL']['points'],cycle['POST_LOCAL']['points']
    pool=before+after;objectives=np.asarray([p['objectives'] for p in pool])
    old=feature_sets(before)['physical'];result=[]
    for slot,p in enumerate(after):
        assert p['lineage']==before[slot]['lineage']
        target=np.asarray(p['objectives']);dominated=np.any(np.all(objectives<=target,axis=1)&np.any(objectives<target,axis=1))
        if p['_physical'] not in old and not dominated:
            result.append(dict(point=p,slot=slot,role=ROLES[slot]))
    return result


def track_endpoints(previous, current, next_pre, paid_uses):
    endpoints=eligible_local(previous)
    g=previous['POST_GLOBAL']['points'];l=previous['POST_LOCAL']['points'];s=previous['SURVIVORS']['points']
    p=current['PRE_GLOBAL']['points'];a=current['POST_GLOBAL']['points']
    collections={label:feature_sets(points) for label,points in [('survivors',s),('nextPre',p),('nextGlobal',a)]}
    memory={x['key'] for x in current['POST_GLOBAL']['memory']}
    results=[]
    for e in endpoints:
        point=e['point'];single=point['_single'];pairs=point['_pairs'];row=dict(key=point['key'],role=e['role'],slot=e['slot'])
        for label,values in collections.items():
            row[label+'Physical']=point['_physical'] in values['physical']
            row[label+'Resources']=point['_r'] in values['resources']
            row[label+'FA']=point['_fa'] in values['FA']
            row[label+'SingleRetained']=len(single&values['singles'])/len(single)
            row[label+'PairRetained']=len(pairs&values['orderedPairs'])/len(pairs)
        row.update(inInternalMemoryExactKey=point['key'] in memory,
                   usedAsCurrent=point['key'] in paid_uses['parent'],
                   usedAsPersonal=point['key'] in paid_uses['donor'],
                   usedAsLeader=point['key'] in paid_uses['teacher'])
        results.append(row)
    counts={k:sum(r[k] for r in results) for k in results[0] if isinstance(results[0][k],bool)} if results else {}
    fractions={k:float(np.median([r[k] for r in results])) for k in results[0] if k.endswith('Retained')} if results else {}
    return dict(fromCycle=previous['POST_LOCAL']['cycle'],toCycle=current['POST_GLOBAL']['cycle'],
                birthFE=previous['POST_LOCAL']['fe'],nextGlobalFE=current['POST_GLOBAL']['fe'],
                candidates=len(results),counts=counts,medianFragmentRetention=fractions,points=results)


def main(root):
    start=time.monotonic();catalog=read(SUPPORT/'sources/models.json')['catalog']
    assert read(SUPPORT/'source-gate.json')['passed'] and read(GAP/'capture-complete.json')['allSixAccepted']
    cycles=load_cycles(catalog);reference=read(GAP/'step1/100_2_3_1-reference.json')
    keys={p['point']['key'] for n in range(4,10) for p in eligible_local(cycles[n])};uses=trace_paid(keys)
    stages=[];transitions=[];geometry=[];endpoints=[]
    for n in range(5,11):
        c=cycles[n];pre,g,l,s=[c[k] for k in ('PRE_GLOBAL','POST_GLOBAL','POST_LOCAL','SURVIVORS')]
        assert g['fe']-pre['fe']==5000
        for name,e in [('PRE_GLOBAL',pre),('POST_GLOBAL',g),('POST_LOCAL',l),('SURVIVORS',s)]:
            values=e['points'];stages.append(dict(cycle=n,fe=e['fe'],phase=name,**metrics(fronts(values),reference,SCALE)))
            geometry.append(dict(cycle=n,fe=e['fe'],phase=name,**cohort(values)))
        for label,before,after in [('QGS',pre['points'],g['points']),('LOCAL',g['points'],l['points']),
                ('POOL_TO_SURVIVORS',g['points']+l['points'],s['points']),
                ('LOCAL_TO_SURVIVORS',l['points'],s['points']),('SURVIVORS_TO_NEXT_PRE',s['points'],cycles[n+1]['PRE_GLOBAL']['points'])]:
            transitions.append(dict(cycle=n,transition=label,quality=compare(before,after,reference),
                retention=retention(before,after),freePairGeometry=pair_motion([p for p in before if p['family']==-1],
                                                                           [p for p in after if p['family']==-1])))
        endpoints.append(track_endpoints(cycles[n-1],c,cycles[n+1]['PRE_GLOBAL'],uses[n]))
        print('CYCLE_ANALYZED',n,flush=True)
    pa=[];models=rows(SUPPORT/'pa-source/models.jsonl')
    events=[r for r in stream(SUPPORT/'pa-source/trajectory-events.jsonl') if r['kind']=='population' and r['label']=='PA_MODEL']
    assert len(models)==len(events)
    for m,e in zip(models,events):
        if not 99540<=e['fe']<=250000:continue
        for p in m['points']:p['family']=-1;describe(p,catalog)
        pa.append(dict(fe=e['fe'],model=m['model'],**cohort(m['points']),
                       quality=metrics(fronts(m['points']),reference,SCALE)))
    output=root/'analysis-v2';output.mkdir()
    for name,value in [('stages',stages),('transitions',transitions),('geometry',geometry),('endpoints',endpoints),('pa-models',pa)]:write(output/(name+'.json'),value)
    csv_write(output/'stage-quality.csv',stages)
    write(output/'acceptance.json',dict(passed=True,source='same instance/seed, old paid full pipeline and PA prefix only',
          cycles=[5,6,7,8,9,10],newFE=0,newDecoderQA=0,newObjectiveQueries=0,
          selectedAndNextPrePhysicalMultisetsExact=True,scope='descriptive associations, not causal effect',
          inputHashes={str(p):sha(p) for p in (SHARE,SUPPORT/'pa-source/models.jsonl',SUPPORT/'pa-source/trajectory-events.jsonl',
                      GAP/'capture/SHARE_CTX_GOM/trajectory-paid.csv',GAP/'step1/100_2_3_1-reference.json')},seconds=time.monotonic()-start))
    print('HISTORY_ANALYSIS_COMPLETE',time.monotonic()-start,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)

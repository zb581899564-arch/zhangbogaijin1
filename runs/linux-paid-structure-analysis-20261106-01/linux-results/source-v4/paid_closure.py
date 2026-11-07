"""Bounded algebraic closure of already-paid factory records, never decoder/search."""
import argparse
from itertools import product
from pathlib import Path
import sys
import time
import numpy as np
from common import BASE, RUN, SOURCE, MATURE, STEMS, SEEDS, ARMS, FACTORY, prepare, read, write, rows, sha
from features import factory_order

MAX_EXPANDED = 1_000_000
MAX_FRONT = 50_000
KERNEL = BASE/'runs/linux-family-support-closure-20261106-01/oracle-code-v2'


def collect(folder, include_paid):
    before=read(folder/'before.json')
    factories=len(before[0]['factoryMakespan'])
    pools=[{} for _ in range(factories)]
    source_rows=[('ENTRY',r['stateId'],r) for r in before]
    if include_paid:
        source_rows.extend(('PAID',r['fe'],r) for r in rows(folder/'paid.jsonl') if r['fe']<=4095)
    for origin,identity,r in source_rows:
        for f in range(factories):
            jobs=factory_order(r,f)
            sig=tuple((j,r['resources'][j]) for j in jobs)
            obj=[r[k][f] for k in FACTORY]
            if sig in pools[f]:
                assert pools[f][sig]['objectives']==obj, 'Factory locality inconsistent'
                continue
            pools[f][sig]=dict(origin=origin,id=identity,objectives=obj,jobs=jobs,
                               resources=[r['resources'][j] for j in jobs],
                               sourceGlobalObjectives=r['objectives'],sourceFresh=r.get('fresh'))
    return [list(p.values()) for p in pools]


def algebra(factors):
    from frontier import objective_powers,encode,decode,pareto
    powers=objective_powers([r for group in factors for r in group])
    reduced=[]
    for group in factors:
        keep=pareto([(*encode(r['objectives'],powers),i) for i,r in enumerate(group)])
        reduced.append([group[r[3]] for r in keep])
    front=[(0,0,0,())]
    stages=[]
    expanded_total=0
    for f,group in enumerate(reduced):
        count=len(front)*len(group)
        if expanded_total+count>MAX_EXPANDED or len(front)>MAX_FRONT:
            return dict(complete=False,reason='Declared algebraic resource bound',stages=stages,
                        inputCounts=list(map(len,factors)),localCounts=list(map(len,reduced)),
                        expanded=expanded_total,nextExpansion=count)
        values=[encode(r['objectives'],powers) for r in group]
        expanded=[(max(a[0],b[0]),a[1]+b[1],a[2]+b[2],a[3]+(i,))
                  for a in front for i,b in enumerate(values)]
        front=pareto(expanded)
        expanded_total+=count
        stages.append(dict(factory=f,expanded=count,retained=len(front)))
    return dict(complete=True,points=[decode(v[:3],powers) for v in front],
                combinations=[list(v[3]) for v in front],factors=reduced,stages=stages,
                inputCounts=list(map(len,factors)),localCounts=list(map(len,reduced)),expanded=expanded_total)


def score(closure,background,scale,reference):
    from analysis_metrics import metrics,pair
    from volume import UncoveredVolume
    if not closure['complete']:
        return None
    initial=metrics(background,reference,scale)
    combined=metrics([*background,*closure['points']],reference,scale)
    best={}
    for radius in (1.25,1.5,2.0):
        scorer=UncoveredVolume(scale.normalize(background),[radius]*3)
        gains=scorer.gains(scale.normalize(closure['points']))
        i=int(np.argmax(gains))
        best[str(radius)]=dict(index=i,objectives=closure['points'][i],absolute=float(gains[i]),
             relativePct=100*float(gains[i])/scorer.background_hv,
             sources=[closure['factors'][f][j] for f,j in enumerate(closure['combinations'][i])])
    return dict(bestSingle=best,withA0=combined,comparison=pair(0,combined,initial),
                scope='Retrospective algebra over paid local objectives; no full decode or algorithm claim; original reference fixed')


def main(root):
    prepare()
    sys.path.append(str(KERNEL))
    from frontier import engineering_checks
    from analysis_metrics import frozen_scale
    output=root/'paid-closure'
    output.mkdir()
    write(output/'scope.json',dict(newSearchFE=0,newDecodes=0,
         futureInformationAllowedOnlyForOfflineCapacity=True,sourceScope='All paid production, excluding terminal composition',
         maxExpandedPerClosure=MAX_EXPANDED,maxFront=MAX_FRONT,
         kernelSHA256=sha(KERNEL/'frontier.py'),fixtures=engineering_checks(),
         floatingQualification='Exact dyadic sums of recorded factory doubles, not bitwise complete decoder predictions'))
    specs={s['stem']:s for s in read(MATURE/'protocol.json')['instances']}
    start=time.perf_counter()
    summary=[]
    for stem in STEMS:
        scale=frozen_scale(specs[stem])
        reference=read(RUN/'analysis'/(stem+'-reference.json'))
        for seed in SEEDS:
            background=read(SOURCE/'inputs-v2'/stem/str(seed)/'0/background.json')
            # Entry is identical for all arms; calculate this control only once.
            for arm in ('ENTRY',*ARMS):
                folder=RUN/'science'/stem/str(seed)/('GOM' if arm=='ENTRY' else arm)
                closure=algebra(collect(folder,arm!='ENTRY'))
                scores=score(closure,background,scale,reference)
                name=f'{stem}-{seed}-{arm}'
                write(output/(name+'.json'),dict(closure=closure,metrics=scores))
                item=dict(instance=stem,seed=seed,arm=arm,complete=closure['complete'],
                          inputCounts=closure['inputCounts'],localCounts=closure['localCounts'],expanded=closure['expanded'])
                if scores:
                    item['bestSingleHVPct']=scores['bestSingle']['1.5']['relativePct']
                    item['unionHVPct']=scores['comparison']['HVEffectPct']['1.5']
                    item['frontSize']=len(closure['points'])
                summary.append(item)
                print('PAID_CLOSURE',item,flush=True)
    write(output/'summary.json',dict(cases=summary,seconds=time.perf_counter()-start,newSearchFE=0,newDecodes=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)

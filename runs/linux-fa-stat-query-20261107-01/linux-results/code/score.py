"""Joint indicators, unchanged acceptance formula, and the predeclared decision."""
import numpy as np
import moocore
from common import *


def hv(points,ref=1.5):
    return float(moocore.hypervolume(np.asarray(points)/SCALE,ref=[ref]*3))


def improvement(a,b):
    return 200*(b-a)/(a+b) if a+b else 0.


def accepts(role,child,parent,archive):
    if role!='CENTER':return child[{'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}[role]]<parent[{'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}[role]]
    weak=all(a<=b for a,b in zip(child,parent))
    dominated=any(all(a<=b for a,b in zip(p,child)) and any(a<b for a,b in zip(p,child)) for p in archive)
    return weak or not dominated


def paired(a,b,reference):
    ma,mb=metrics(a,reference,SCALE),metrics(b,reference,SCALE)
    changes={str(ref):100*(hv(a,ref)/hv(b,ref)-1) for ref in (1.25,1.5,2.0)}
    ab,ba=coverage(a,b),coverage(b,a)
    return dict(HVpercent=changes['1.5'],HVsensitivity=changes,
        IGDplusImprovementPercent=improvement(ma['IGDplus'],mb['IGDplus']),
        IGDplusAbsoluteReduction=mb['IGDplus']-ma['IGDplus'],
        IGDImprovementPercent=improvement(ma['IGD'],mb['IGD']),C_A_B=ab,C_B_A=ba,
        coverageDifferencePP=100*(ab['C']-ba['C']))


def outcome(entry,arm,background,queries,actual,reference):
    selected=[q for q in queries.values() if q['context']==entry['id'] and q['arm']==arm]
    parent={p['slot']:p for p in entry['S']};base=entry[background];base_hv=hv(base)
    points=[];accepted=[];single=[]
    for q in selected:
        obj=actual[q['id']]['objectives'];points.append(obj)
        keep=accepts(q['role'],obj,parent[q['receiver']]['objectives'],entry['S_archive'])
        if keep:accepted.append(obj)
        fresh=not any(all(a<=b for a,b in zip(p,obj)) for p in base)
        single.append(dict(id=q['id'],context=entry['id'],arm=arm,role=q['role'],
            background=background,wouldAccept=keep,fresh=fresh,maskSize=len(q['fos']),fallback=q['fallback'],
            changedResourceJobs=sum(a!=b for a,b in zip(q['resources'],parent[q['receiver']]['resources'])),
            singleDeltaHV=hv([*base,obj])-base_hv if fresh else 0.))
    front=nd([*base,*points]);accepted_front=nd([*base,*accepted])
    return front,accepted_front,dict(context=entry['id'],arm=arm,background=background,FE=len(selected),
        base=metrics(base,reference,SCALE),final=metrics(front,reference,SCALE),
        acceptedOnly=metrics(accepted_front,reference,SCALE),accepted=sum(r['wouldAccept'] for r in single),
        fresh=sum(r['fresh'] for r in single),freshAccepted=sum(r['fresh'] and r['wouldAccept'] for r in single),
        deltaHV=hv(front)-base_hv,relativeGainHVpercent=100*(hv(front)/base_hv-1),
        meanMaskSize=float(np.mean([r['maskSize'] for r in single])),fallbacks=sum(q['fallback'] for q in selected),
        extrema=[front[np.argmin(front[:,k])].tolist() for k in range(3)]),single


def decision(comparisons):
    result=[]
    for control in ('POST_FA','RANDOM_FOS'):
        values=[r for r in comparisons if r['background']=='S_archive' and r['control']==control]
        signals=[];adverse=[];flips=[]
        for r in values:
            bad=r['HVpercent']<-.1 or r['IGDplusImprovementPercent']<-5 or r['coverageDifferencePP']<-10
            flip=any(r['HVpercent']*r['HVsensitivity'][str(ref)] < -1e-18 for ref in (1.25,2.0))
            if bad:adverse.append(r['context'])
            if flip:flips.append(r['context'])
            if (r['HVpercent']>=.1 or r['IGDplusImprovementPercent']>=5) and not bad and not flip:signals.append(r['context'])
        result.append(dict(control=control,signalContexts=signals,majorReverseContexts=adverse,
                           HVReferenceFlipContexts=flips,passed=len(signals)>=2 and not adverse))
    passed=all(r['passed'] for r in result)
    return dict(continueHypothesis=passed,decision='RETAIN_CONDITIONAL_CAPACITY_HYPOTHESIS' if passed else 'STOP_FIXED_FA_STAT_SOURCE_HYPOTHESIS',
        comparisons=result,fullAlgorithmPromoted=False,mainlineChanged=False,independentSeeds=1,correlatedContexts=3,
        rule='Both direct and size-matched random controls must pass the frozen joint-indicator criteria')

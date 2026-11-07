"""Joint endpoint indicators and physical-domain attribution; never feeds search."""
import argparse
from collections import Counter
from pathlib import Path
from statistics import median
import sys
import time
import numpy as np
from common import SOURCE,MATURE,ANCHOR,STEMS,SEEDS,ARMS,linux,read,write,lines,sha
from audit_generation import domain_check,outside


def supply(folder,background,scale):
    from research.dynamic_benchmark.metrics import nondominated
    from volume import UncoveredVolume
    before=read(folder/'before.json');receipt=read(folder/'receipt.json');steps=lines(folder/'steps.jsonl')
    stem=folder.parent.parent.name;domain=domain_check(read(folder/'domain.json'),before,stem,receipt['seed'])
    candidates=[];counts=Counter();live={r['slot']:r for r in before}
    for row in steps:
        parent=live[row['slot']];kind=outside(row,domain);counts[kind]+=1
        changed_resource=row['resources']!=parent['resources']
        changed_order=any([j for j,f in zip(row['JS'],row['FA']) if f==ff]!=
            [j for j,f in zip(parent['JS'],parent['FA']) if f==ff] for ff in range(len(domain['jobs'])))
        counts['resourceChanged']+=changed_resource;counts['physicalOrderChanged']+=changed_order
        counts['physicalNoop']+=not changed_resource and not changed_order
        if kind!='INSIDE':
            candidates.append(row['objectives']);counts['outsideArchiveAdmissions']+=row['fresh']
            counts['outsideAccepted']+=row['accepted']
        if row['accepted']:live[row['slot']]=row
    paid=lines(folder/'paid.jsonl');paid_front=nondominated([r['objectives'] for r in paid])
    best={};candidate_front=nondominated(candidates) if candidates else np.empty((0,3))
    for radius in (1.25,1.5,2.0):
        scorer=UncoveredVolume(scale.normalize(background),[radius]*3)
        gains=scorer.gains(scale.normalize(candidate_front));index=int(np.argmax(gains)) if len(gains) else None
        best[str(radius)]=dict(objectives=candidate_front[index].tolist() if index is not None else None,
            absolute=float(gains[index]) if index is not None else 0.,
            relativePct=100*float(gains[index])/scorer.background_hv if index is not None else 0.)
    assembly=read(folder/'assembly.json');initial=read(folder/'initial-pools.json')['initialSelection']
    chosen=assembly['chosen'];production=receipt['plannedProductionFE']
    fresh_chosen=sum(r is not None and r['stage']=='PROBE_PAID' and 1<=r['paidFE']<=production for r in chosen)
    return dict(counts=dict(counts),bestSingleOutsideProduction=best,paidOnly=paid_front.tolist(),
        working=[r['objectives'] for r in read(folder/'after.json')],
        initialAssemblyFeasible=initial['feasible'],finalAssemblyFeasible=assembly['feasible'],
        terminalObjectives=assembly['result']['objectives'],chosenNewFactoryRecords=fresh_chosen,
        scope='Outside membership relative to initial five; best single excludes terminal assembly; all reporting endpoints include every paid evaluation')


def instance(root,spec):
    from analysis_metrics import metrics,frozen_scale,pair
    from audit_metrics import endpoint_metrics,raw_coverage,close
    from research.dynamic_benchmark.metrics import nondominated
    stem=spec['stem'];scale=frozen_scale(spec)
    fronts={(seed,arm):read(root/'science'/stem/str(seed)/arm/'front.json') for seed in SEEDS for arm in ARMS}
    reference=nondominated(np.vstack(list(fronts.values())));write(root/'analysis'/(stem+'-reference.json'),reference.tolist())
    observations=[];values={};checks=0
    for (seed,arm),front in fronts.items():
        folder=root/'science'/stem/str(seed)/arm
        a0=read(SOURCE/'inputs-v2'/stem/str(seed)/'0/background.json')
        s=supply(folder,a0,scale);endpoint=metrics(front,reference,scale);background=metrics(a0,reference,scale)
        for name,raw in [('final',front),('paidOnly',s.pop('paidOnly')),('working',s.pop('working'))]:
            m=endpoint if name=='final' else metrics(raw,reference,scale)
            independent,_=endpoint_metrics(np.asarray(m['front']),reference,spec['normalization'])
            for radius in ('1.25','1.5','2.0'):close(m['HV'][radius],independent['HV'][radius],'independent endpoint HV');checks+=1
            s[name]=m
        # Independently verify every reported best-single effect with a full HV union calculation.
        for radius,best in s['bestSingleOutsideProduction'].items():
            if best['objectives'] is not None:
                union=metrics([*a0,best['objectives']],reference,scale)
                close(best['absolute'],union['HV'][radius]-background['HV'][radius],'single-point union HV');checks+=1
        values[seed,arm]=endpoint;r=read(folder/'receipt.json')
        observations.append(dict(seed=seed,arm=arm,A0=background,aboveA0=pair(seed,endpoint,background),supply=s,
            successfulFE=r['successful'],searchSecondsIncludesQA=r['searchSeconds'],
            physicsQASeconds=r['physicsQA']['engineeringOnlySeconds'],
            observationSeconds=r['paidEvidenceSeconds']+r['stepEvidenceSeconds'],
            processSeconds=read(folder/'process.json')['seconds'],importQA=r['importQA']))
    comparisons=[]
    for a,b in [('NOVEL','LEGAL'),('LEGAL','GOM'),('NOVEL','GOM')]:
        pairs=[pair(seed,values[seed,a],values[seed,b]) for seed in SEEDS]
        for seed,p in zip(SEEDS,pairs):
            coverage=raw_coverage(values[seed,a]['front'],values[seed,b]['front'])
            for key in ('C_A_B','C_B_A','coveredA','coveredB','totalA','totalB'):assert p['coverage'][key]==coverage[key]
        median_hv={r:float(median(p['HVEffectPct'][r] for p in pairs)) for r in ('1.25','1.5','2.0')}
        comparisons.append(dict(candidate=a,control=b,pairs=pairs,medianHV=median_hv,
            medianIGDplus=float(median(p['IGDplusSymmetricImprovementPct'] for p in pairs)),
            medianCgapPP=100*float(median(p['Cdelta'] for p in pairs)),
            hvWins=sum(p['HVEffectPct']['1.5']>0 for p in pairs),igdPlusWins=sum(p['IGDplusSymmetricImprovementPct']>0 for p in pairs)))
    return dict(instance=stem,referenceSize=len(reference),normalization=spec['normalization'],observations=observations,
        comparisons=comparisons,independentHVChecks=checks,
        materialCapacity={a:sum(o['supply']['bestSingleOutsideProduction']['1.5']['relativePct']>=.1 for o in observations if o['arm']==a) for a in ARMS})


def main(root):
    linux();assert read(root/'science-independent-audit.json')['passed'];out=root/'analysis';out.mkdir()
    sys.path.insert(1,str(ANCHOR/'payload'));sys.path.insert(2,str(MATURE/'analysis-code'))
    started=time.perf_counter();results=[]
    for spec in read(MATURE/'protocol.json')['instances']:
        result=instance(root,spec);results.append(result);print('DOMAIN_METRICS_DONE',spec['stem'],flush=True)
    capacity=any(r['materialCapacity'][a]>=2 for r in results for a in ('LEGAL','NOVEL'))
    decision='CAPACITY_PRESENT_REVIEW_JOINT_INDICATORS' if capacity else 'STOP_FIXED_TWO_JOB_DOMAIN_PRODUCER'
    write(out/'report.json',dict(instances=results,decision=decision,seconds=time.perf_counter()-started,
        smallDevelopmentProbe=True,completeAlgorithmClaim=False,sameTimeClaim=False,newEvaluationQueries=0,
        sourceReuse='Six previously paid source families; no independent test or generalized same-FA upper bound'))
    for r in results:
        print('CAPACITY',r['instance'],r['materialCapacity'])
        print('PAIRS',[(p['candidate'],p['control'],p['medianHV']['1.5'],p['medianIGDplus'],p['medianCgapPP']) for p in r['comparisons']])
    print('DECISION',decision,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)

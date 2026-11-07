"""Joint indicators and request diagnostics; no search feedback or weighted score."""
import argparse
import csv
from pathlib import Path
from statistics import median
import sys
import time
import numpy as np
from common import ANCHOR, SOURCE, STEMS, SEEDS, linux, read, write
from protocol import ARMS

COMPARISONS=[('REQUEST','ROLE'),('REQUEST','ORDINARY'),('REQUEST','SHUFFLED'),('ORDINARY','ROLE')]


def supply(folder):
    first,last=read(folder/'initial-pools.json'),read(folder/'final-pools.json')
    assembly=read(folder/'assembly.json');receipt=read(folder/'receipt.json')
    def produced(record):
        return record is not None and record['stage']=='PROBE_PAID' and 1<=record['paidFE']<=511
    retained=[r for f in last['factories'] for r in f['records'] if produced(r)]
    chosen=assembly['chosen']
    return dict(initialFeasible=first['initialSelection']['feasible'], finalFeasible=assembly['feasible'],
        initialPredicted=first['initialSelection']['predicted'], finalPredicted=assembly['predicted'],
        newRetainedFactoryRecords=len(retained),
        retainedScope='Production-origin records still retained after the terminal assembly/fallback offer; excludes FE512 and imported records',
        chosenNewFactories=sum(produced(r) for r in chosen),
        acceptanceChanges=receipt['acceptance'].get('changedVersusOriginalRole',0),
        feasiblePaidProduction=receipt['acceptance'].get('candidateFeasible',0),
        acceptance=receipt['acceptance'],actualCap=receipt['actualRequest']['cap'],
        effectiveCap=receipt['effectiveRequest']['cap'],
        capMismatch=receipt['actualRequest']['cap']!=receipt['effectiveRequest']['cap'])


def csv_write(path,rows):
    if not rows:return
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def paired_summary(pairs):
    def collapse(key):
        perseed=[dict(seed=seed,median=float(median(p[key] for p in pairs if p['seed']==seed))) for seed in SEEDS]
        values=[r['median'] for r in perseed]
        return dict(perSeed=perseed,median=float(median(values)),range=[min(values),max(values)],
                    wins=sum(v>0 for v in values),ties=sum(v==0 for v in values),losses=sum(v<0 for v in values))
    return {k:collapse(k) for k in ('HV','HV125','HV200','IGDplus','CgapPP')}


def instance(root,spec):
    from analysis_metrics import metrics, frozen_scale, pair
    from audit_metrics import endpoint_metrics, raw_coverage, close
    from research.dynamic_benchmark.metrics import nondominated
    stem=spec['stem'];scale=frozen_scale(spec)
    fronts={(seed,q,arm):read(root/'science'/stem/str(seed)/str(q)/arm/'front.json')
            for seed in SEEDS for q in range(3) for arm in ARMS}
    reference=nondominated(np.vstack(list(fronts.values())))
    observations=[];measures={};flat=[];check_count=0
    for (seed,q,arm),front in fronts.items():
        folder=root/'science'/stem/str(seed)/str(q)/arm
        value=metrics(front,reference,scale)
        independent,errors=endpoint_metrics(np.asarray(value['front']),reference,spec['normalization'])
        for radius in ('1.5','1.25','2.0'):close(value['HV'][radius],independent['HV'][radius],'independent HV')
        check_count+=3
        measures[seed,q,arm]=value
        background=metrics(read(root/'inputs-v2'/stem/str(seed)/str(q)/'background.json'),reference,scale)
        assert all(v>0 for v in background['HV'].values()), 'Zero-HV A0: relative-effect report requires an explicit unavailable policy'
        assert value['HV']['1.5']>=background['HV']['1.5']-1e-12
        working=metrics([r['objectives'] for r in read(folder/'after.json')],reference,scale)
        receipt=read(folder/'receipt.json')
        observations.append(dict(seed=seed,requestIndex=q,arm=arm,final=value,working=working,A0=background,
            supply=supply(folder),actualFE=receipt['successful'],searchSeconds=receipt['searchSeconds'],
            preparationSeconds=receipt['prepareSeconds'],processSeconds=read(folder/'process.json')['seconds']))
        flat.append(dict(instance=stem,seed=seed,request=q,arm=arm,HV=value['HV']['1.5'],
            IGDplus=value['IGDplus'],IGD=value['IGD'],frontSize=value['frontSize'],
            HVAboveA0=value['HV']['1.5']-background['HV']['1.5'],
            Cmax=value['objectiveMinimum'][0],TEC=value['objectiveMinimum'][1],TWC=value['objectiveMinimum'][2]))
    comparisons=[];pair_rows=[]
    for a,b in COMPARISONS:
        pairs=[]
        for seed in SEEDS:
            for q in range(3):
                av,bv=measures[seed,q,a],measures[seed,q,b]
                p=pair(seed,av,bv);raw=raw_coverage(av['front'],bv['front'])
                for key in ('C_A_B','C_B_A','coveredB','coveredA','totalB','totalA'):
                    assert p['coverage'][key]==raw[key]
                v=dict(instance=stem,seed=seed,request=q,candidate=a,control=b,
                    HV=p['HVEffectPct']['1.5'],HV125=p['HVEffectPct']['1.25'],HV200=p['HVEffectPct']['2.0'],
                    IGDplus=p['IGDplusSymmetricImprovementPct'],CgapPP=100*p['Cdelta'],
                    C_A_B=raw['C_A_B'],C_B_A=raw['C_B_A'],coveredB=raw['coveredB'],totalB=raw['totalB'],
                    coveredA=raw['coveredA'],totalA=raw['totalA'])
                pairs.append(v);pair_rows.append(v)
        regimes={str(q):dict(capFactor=[.9,1,1.1][q],eta=[0,1,4][q],
                    summary=paired_summary([p for p in pairs if p['request']==q])) for q in range(3)}
        comparisons.append(dict(candidate=a,control=b,pairs=pairs,summary=paired_summary(pairs),
            requestRegimes=regimes,regimeScope='Descriptive decomposition of fixed sampled cycles; does not replace pooled primary endpoint'))
    return dict(instance=stem,normalization=spec['normalization'],reference=reference.tolist(),
        referenceRule='ND union all four arms x three requests x three source seeds final reporting fronts',
        observations=observations,comparisons=comparisons,independentHVChecks=check_count),flat,pair_rows


def main(root):
    linux();assert read(root/'science-complete.json')['passed']
    assert read(root/'science-independent-audit.json')['passed']
    sys.path.insert(0,str(ANCHOR/'payload'));sys.path.insert(0,str(SOURCE/'analysis-code'))
    started=time.perf_counter();cases=[];flat=[];pairs=[]
    for spec in read(SOURCE/'protocol.json')['instances']:
        result,rows,paired=instance(root,spec);cases.append(result);flat.extend(rows);pairs.extend(paired)
        print('REQUEST_ANALYSIS_CASE',spec['stem'],flush=True)
    out=root/'report';out.mkdir(exist_ok=False)
    write(out/'analysis.json',dict(instances=cases,seconds=time.perf_counter()-started,
        newSearchFE=0,newDecodes=0,independentHVChecks=sum(c['independentHVChecks'] for c in cases),
        aggregation='Within each source seed, median of three paired requests; then median/range of three seed effects',
        independentSeedCount=3,requestContextsPerInstance=9,sameTimeClaim=False,
        completeAlgorithmClaim=False,sourceStatesIndependentValidation=False))
    csv_write(out/'metrics.csv',flat);csv_write(out/'pairs.csv',pairs)
    write(out/'summary.json',[dict(instance=c['instance'],comparisons=[{k:v for k,v in r.items() if k!='pairs'} for r in c['comparisons']]) for c in cases])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    main(parser.parse_args().root)

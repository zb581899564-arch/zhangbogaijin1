"""Post-batch descriptive checks, not extra searches or preregistered winner gates."""
from pathlib import Path
import argparse
import csv
import json
import platform
import sys
import time
import numpy as np

for parent in Path(__file__).resolve().parents:
    if (parent/'research/pilot_evaluation').is_dir():
        sys.path.insert(0,str(parent));break

from run_support import read,rows,write
from exact_hv import exact_hv
from research.pilot_evaluation import igd,igd_plus,exact_coverage,igd_plus_symmetric_effect


def prefix_front(path,limit):
    front=np.empty((0,3));seen=0
    with path.open() as f:
        for r in csv.DictReader(f):
            fe=int(r['fe'])
            if fe>limit:break
            seen=fe
            if r['admitted']=='1':
                p=np.array([float(r[k]) for k in ['Cmax','TEC','TWC']])
                if len(front) and np.any(np.all(front<=p,axis=1)):continue
                front=np.vstack((front[~np.all(p<=front,axis=1)],p))
    assert seen==limit
    return front


def tuple_use(path):
    initial=rows(path/'initial-population.jsonl');support={j:set() for j in initial[0]['JS']}
    def tuples(row):return zip(row['JS'],zip(row['FA'],row['MA'],row['WA']))
    for row in initial:
        for job,tup in tuples(row):support[job].add(tup)
    final=[r for r in rows(path/'checkpoint-solutions.jsonl') if r['checkpointKind']=='FE' and r['checkpoint']==500000]
    counts=[sum(tup not in support[job] for job,tup in tuples(r)) for r in final]
    return {'finalSavedRepresentatives':len(final),'representativesUsingAnyNoninitialFMW':sum(x>0 for x in counts),
            'noninitialTupleCountAcrossRepresentatives':sum(counts),'totalJobTuples':len(counts)*len(support),
            'initialDistinctTuplesPerJob':{str(j):len(t) for j,t in support.items()},
            'interpretation':'Use in one saved representative, not proof that equal-quality schedules require these tuples'}


def main(root):
    if platform.system()!='Linux':raise RuntimeError('Linux only')
    start=time.perf_counter();plan=read(root/'protocol.json');report=root/'report'
    assert read(report/'summary.json')['scienceSuccessfulFE']==9000000
    references=read(report/'reference-fronts.json')
    metrics=read(report/'final-metrics.json')
    index={(r['instance'],r['seed'],r['arm']):r for r in metrics}
    results=[];tuples=[]
    for spec in plan['instances']:
        stem=spec['stem'];scale=np.array(spec['normalization']['scale'])
        reference=np.array(references[stem]['normalized_objectives'])
        for seed in plan['seeds']:
            base=root/'science'/stem/str(seed)
            full=index[stem,seed,'FULL'];receipt=rows(base/'FULL/run-receipt.jsonl')[0]
            local_fe=receipt['trace']['phaseFE']['LOCAL'];target=100+local_fe
            prefix=prefix_front(base/'LOCAL_ONLY/paid-events.csv',target);normal=prefix/scale
            phv=exact_hv(normal,[1.5]*3);pd=igd_plus(normal,reference)
            results.append({'instance':stem,'seed':seed,'fullTotalFE':500000,'fullLocalFE':local_fe,
                'localOnlyTotalFEMatched':target,'fullHV':full['HV'],'localOnlyMatchedHV':phv,
                'fullHVRelativePercent':100*(full['HV']/phv-1),
                'fullIGDplus':full['IGDplus'],'localOnlyMatchedIGDplus':pd,
                'fullIGDplusSymmetricImprovementPercent':100*igd_plus_symmetric_effect(full['IGDplus'],pd),
                'localOnlyMatchedIGD':igd(normal,reference),
                **exact_coverage(full['rawFront'],prefix)})
            for arm in plan['arms']:
                tuples.append({'instance':stem,'seed':seed,'arm':arm,**tuple_use(base/arm)})
    write(report/'phase-explanation.json',{'posthoc':True,'newSearchFE':0,'newDecoderCalls':0,
        'localBudgetAligned':results,'initialResourceSupportUse':tuples,'offlineSeconds':time.perf_counter()-start,
        'limitations':['Equal local FE is not equal total FE or time; descriptive only, not a leaderboard',
                       'Different global work consumes different RNG and changes donor/population states; no pure disruption causal claim',
                       'Saved genotype support use does not prove representation necessity; do not select algorithms by these two instances']})
    print('PHASE_EXPLANATION_COMPLETE',len(results),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);main(p.parse_args().root.resolve())

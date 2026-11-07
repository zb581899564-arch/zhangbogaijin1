"""Zero-evaluation structural description: E/W ranking disagreement and two-objective projection loss."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT, read, rows, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume

TIME_SOURCE=ROOT/'runs/snapshot-true-time-bench-20261105-052344-318911'
POOL_SOURCE=ROOT/'runs/mating-pool-probe-20261105-062648-478040'
STEMS=('20_8_5_1','100_2_3_1');SEEDS=(11610003,11610033,11610063)
METHODS=('FULL_ANCHOR','NSGA_ANCHOR');CHECKS=(100,5100,100000);REFERENCES=(1.25,1.5,2.0)


def projection_indices(points,columns):
    """Exact two-dimensional ND; duplicate projections retain the best omitted coordinate."""
    missing=next(k for k in range(3) if k not in columns)
    order=sorted(range(len(points)),key=lambda i:tuple(points[i,k] for k in (*columns,missing)))
    keep=[];minimum=float('inf')
    for i in order:
        if points[i,columns[1]]<minimum:keep.append(i);minimum=points[i,columns[1]]
    return keep


def brute_projection(points,columns):
    selected=[]
    for i,p in enumerate(points):
        if any(np.all(q[list(columns)]<=p[list(columns)]) and np.any(q[list(columns)]<p[list(columns)]) for q in points):continue
        same=[j for j,q in enumerate(points) if np.array_equal(q[list(columns)],p[list(columns)])]
        missing=next(k for k in range(3) if k not in columns)
        if i==min(same,key=lambda j:(points[j,missing],j)):selected.append(i)
    return set(selected)


def engineering():
    fixtures=[np.array([[1.,3.,9.],[1.,3.,4.],[2.,2.,7.],[3.,1.,8.],[4.,4.,1.]]),
              np.array([[0.,0.,0.]]),np.array([[1.,1.,1.],[1.,1.,1.],[2.,2.,2.]])]
    for points in fixtures:
        for columns in ((0,1),(0,2)):assert set(projection_indices(points,columns))==brute_projection(points,columns)
    return {'status':'PASS','projectionFixtures':len(fixtures)*2,'searchFE':0,'decodes':0}


def correlation(points):
    def rank(values):
        _,inverse,counts=np.unique(values,return_inverse=True,return_counts=True)
        centers=np.cumsum(counts)-counts/2
        return centers[inverse]
    a,b=rank(points[:,1]),rank(points[:,2])
    return float(np.corrcoef(a,b)[0,1]) if np.std(a)>0 and np.std(b)>0 else None


def front_row(stem,seed,method,point,spec,independent):
    values=np.unique(np.asarray(point['front'],dtype=float),axis=0)
    if len(values)==0 or not np.isfinite(values).all():raise ValueError('Missing finite paid front')
    norm=spec['normalization'];normalized=(values-norm['lower'])/norm['scale']
    result={'stem':stem,'seed':seed,'method':method,'kind':point['checkpointKind'],'checkpoint':point['checkpoint'],
            'actualFE':point['fe'],'frontSize':len(values),'energyWageSpearman':correlation(values),'projections':{}}
    for label,columns in (('C_E',(0,1)),('C_W',(0,2))):
        ids=projection_indices(values,columns)
        if independent:assert set(ids)==brute_projection(values,columns)
        measures=[]
        for ref in REFERENCES:
            full=UncoveredVolume(normalized,(ref,)*3).background_hv
            retained=UncoveredVolume(normalized[ids],(ref,)*3).background_hv
            assert retained<=full+1e-11 and retained>=-1e-11
            if independent:
                assert abs(full-hypervolume(normalized,(ref,)*3))<1e-11
                assert abs(retained-hypervolume(normalized[ids],(ref,)*3))<1e-11
            measures.append({'reference':ref,'fullHV':full,'retainedHV':retained,
                             'lossPct':100*max(0.,full-retained)/full if full>1e-12 else None})
        result['projections'][label]={'retainedSize':len(ids),'retainedIndices':ids,'measures':measures}
    return result


def pool_rows(root,stem):
    results=[]
    for context in read(POOL_SOURCE/stem/'contexts.json'):
        values=np.asarray([p['objectives'] for p in context['current']]);a,b=np.triu_indices(len(values),1)
        e=np.sign(values[a,1]-values[b,1]);w=np.sign(values[a,2]-values[b,2]);strict=(e!=0)&(w!=0)
        inversions=int(np.sum(e*w<0));n=int(np.sum(strict))
        results.append({'stem':stem,'context':context['contextId'],'seed':context['seed'],'step':context['step'],
            'preBatchFE':context['preBatchFE'],'poolSize':len(values),'pairCount':len(a),'strictBothPairs':n,
            'energyWageOppositePairs':inversions,'oppositePctOfStrict':100*inversions/n if n else None,
            'energyWageSpearman':correlation(values)})
    return results


def main():
    root=ROOT/'runs'/datetime.now().strftime('objective-roles-audit-%Y%m%d-%H%M%S-%f');root.mkdir();print('OBJECTIVE_ROLES_ROOT',root,flush=True)
    shutil.copy2(__file__,root/'run_objective_roles_audit.py')
    specs=read(POOL_SOURCE/'protocol.json')['instances']
    write_once(root/'protocol.json',{'sourceTime':str(TIME_SOURCE),'sourcePools':str(POOL_SOURCE),'instances':specs,
        'seeds':SEEDS,'methods':METHODS,'checkpoints':'Actual FE100/5100/100000 and true finalT4/5s; missing is reported, no substitution.',
        'question':'Are energy and wage empirically identical preferences, and how much original3D coverage is removed by C/E or C/W ND filtering?',
        'projection':'Exact2DND on already-paid3Dfront, equal2Dprojection keeps best omitted coordinate. Score retained original3Dpoints, no model/objective deletion.',
        'poolComparison':'Current80free working parents at all6frozen pre-batch contexts per instance; exact E/W strict-pair rank disagreement.',
        'engineering':'Six synthetic fast-vs-brute projection fixtures; real firstsource finalT per method/instance independent brute projection '
                      'and slowHV at all3references. No decode/newcandidate/search.',
        'limits':'Descriptive reused fronts and correlated points. Nonzero projection loss or strict inversions disprove exact redundancy on these data; '
                 'zero loss on sampledfronts cannot prove global objective redundancy. No new selector or performance gate; no novelty or causal role benefit.',
        'newSearchFE':0,'additionalDecodes':0,'preserved':'No source/default mainline/objective/family/shared rule changes; no network transfer.'})
    write_once(root/'engineering.json',engineering());reports=[];missing=[]
    try:
        for spec in specs:
            stem=spec['stem'];items=[]
            for seed in SEEDS:
                for method in METHODS:
                    source=TIME_SOURCE/stem/f'{seed}-{method}'
                    check=read(source/'checkpoint-validation.json');assert check['status']=='PASS'
                    points=rows(source/'anytime.jsonl')
                    for kind,target in [('FE',f) for f in CHECKS]+[('TIME',float(spec['time_seconds']))]:
                        matches=[p for p in points if p['checkpointKind']==kind and p['checkpoint']==target and p['reached']]
                        if len(matches)!=1:missing.append({'stem':stem,'seed':seed,'method':method,'kind':kind,'checkpoint':target});continue
                        items.append(front_row(stem,seed,method,matches[0],spec,seed==SEEDS[0] and kind=='TIME'))
            pools=pool_rows(root,stem);write_once(root/f'{stem}.json',{'fronts':items,'pools':pools})
            summaries={}
            for label in ('C_E','C_W'):
                losses=[next(m['lossPct'] for m in r['projections'][label]['measures'] if m['reference']==1.5) for r in items if r['kind']=='TIME']
                summaries[label]={'finalTPairedFronts':len(losses),'median3DHVLossPct':float(np.median(losses)),
                                  'min3DHVLossPct':min(losses),'max3DHVLossPct':max(losses)}
            reports.append({'stem':stem,'fronts':len(items),'poolContexts':len(pools),'finalTProjectionLosses':summaries,
                'poolOppositePairPctMin':min(p['oppositePctOfStrict'] for p in pools),
                'poolOppositePairPctMax':max(p['oppositePctOfStrict'] for p in pools)})
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','newSearchFE':0,'additionalDecodes':0,'error':str(error)});raise
    write_once(root/'analysis.json',{'instances':reports,'missing':missing,'newSearchFE':0,'additionalDecodes':0})
    write_once(root/'status.json',{'status':'COMPLETE','fronts':sum(r['fronts'] for r in reports),'missing':missing,'newSearchFE':0,'additionalDecodes':0})
    print('OBJECTIVE_ROLES_COMPLETE',reports,flush=True)


if __name__=='__main__':main()

"""Outcome-declared diagnostic representatives from existing paid fronts, not new algorithm data."""
from pathlib import Path
import numpy as np

SOURCE=Path(__file__).resolve().parents[2]/'runs/makespan-tie-screen-20261105-025223-471920'
REGIONS=Path(__file__).resolve().parents[2]/'runs/search-gap-regions-20261105-033025-648367/analysis.json'


def assignment(point):
    n=len(point['JS']);result=[-1]*n
    assert sorted(point['JS'])==list(range(n))
    for j,f in zip(point['JS'],point['FA']):result[j]=int(f)
    return tuple(result)


def representatives(front,cuts,scale):
    values=np.asarray([p['objectives'] for p in front]);chosen={}
    selectors=[(f'minObjective{k}',int(np.argmin(values[:,k]))) for k in range(3)]
    selectors.extend((f'CmaxQuartile{q}',int(np.argmin(np.abs(values[:,0]/scale[0]-cut)))) for q,cut in enumerate(cuts[1:-1],1))
    for label,index in selectors:
        key=tuple(tuple(front[index][k]) for k in ('JS','FA','MA','WA'))
        if key not in chosen:chosen[key]={'labels':[],'point':front[index]}
        chosen[key]['labels'].append(label)
    return list(chosen.values())


def prepare(spec,seeds,read,rows):
    stem=spec['stem'];scale=spec['normalization']['scale']
    cuts=next(r['empiricalCommonCmaxCuts'] for r in read(REGIONS)['instances'] if r['stem']==stem)
    cohorts=[]
    for seed in seeds:
        main=rows(SOURCE/stem/str(seed)/'STRICT_FULL/solutions.jsonl')
        nsga=rows(SOURCE/stem/str(seed)/'NSGA_STRICT/solutions.jsonl')
        initial=rows(SOURCE/stem/str(seed)/'STRICT_FULL/initial-population.jsonl')
        anchors={};checks=[]
        for family,index in enumerate((0,5,10,15)):
            a=assignment(initial[index]);anchors.setdefault(a,{'assignment':a,'labels':[]})['labels'].append(f'fixedFamily{family}')
        for record in representatives(main,cuts,scale):
            a=assignment(record['point']);anchors.setdefault(a,{'assignment':a,'labels':[]})['labels'].extend('MAIN/'+s for s in record['labels'])
            checks.append({'kind':'MAIN','assignment':a,'objectives':record['point']['objectives']})
        targets=[]
        for record in representatives(nsga,cuts,scale):
            a=assignment(record['point']);checks.append({'kind':'NSGA','assignment':a,'objectives':record['point']['objectives']})
            targets.append({'labels':record['labels'],'objectives':record['point']['objectives'],'ownAssignment':a})
        cohorts.append({'stem':stem,'seed':seed,'anchors':list(anchors.values()),'targets':targets,'selfChecks':checks})
    return {'stem':stem,'commonEmpiricalCuts':cuts,'cohorts':cohorts}

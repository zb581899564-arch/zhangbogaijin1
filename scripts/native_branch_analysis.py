"""Prediction-only scoring precedes outcome loading; all ranking and computation costs retained."""
import time
import numpy as np
from scipy.stats import spearmanr

from run_long_budget_bridge import read,rows,write_once,hypervolume
from research.reachability.cases import assignment
from research.reachability.relaxation import FixedFARelaxation
from research.reachability.separated_bound import separated_bound

METHODS=('GREEDY','TAIL_SUM','TAIL_RAY','CHEAP_RAY','LP_TIME','LP_FATIGUE','RANDOM')


def fixed_resources(genome):
    result=[None]*len(genome['JS'])
    for j,m,w in zip(genome['JS'],genome['MA'],genome['WA']):result[j]=(m,w)
    return result


def score_inputs(root,stem,metadata,seeds):
    scored=[]
    for seed in seeds:
        for feature in rows(root/stem/str(seed)/'probe/features.jsonl'):
            target=np.asarray(feature['parentObjectives']);partial=np.asarray(feature['partial']);tail=np.asarray(feature['tail'])
            fa=assignment(feature['genome']);fixed=fixed_resources(feature['genome']);prefix=feature['prefix'];cost={}
            scores={'GREEDY':float(np.sum(partial/feature['scales'])),
                'TAIL_SUM':float(np.sum((partial+tail)/feature['scales'])),
                'TAIL_RAY':float(np.max((partial+tail)/target))}
            start=time.monotonic();model=FixedFARelaxation(metadata,fa,prefix,fixed_stage_zero=fixed)
            time_bound=model.solve(target);cost['LP_TIME']=time.monotonic()-start
            start=time.monotonic();cheap_model=FixedFARelaxation(metadata,fa,prefix,fixed_stage_zero=fixed)
            cheap=separated_bound(cheap_model,target);cost['CHEAP_RAY']=time.monotonic()-start
            start=time.monotonic();fat_model=FixedFARelaxation(metadata,fa,prefix,float(target[0]),fixed_stage_zero=fixed)
            fat_bound=fat_model.solve(target);fat_seconds=time.monotonic()-start
            scores['CHEAP_RAY']=cheap['dual']['lower'];scores['LP_TIME']=time_bound['dual']['lower']
            # Conditional fatigue coefficients are valid through the parent-C horizon only.
            # Clipping at1 restores a global ray lower bound when the completed C exceeds it.
            scores['LP_FATIGUE']=max(scores['LP_TIME'],min(1.,fat_bound['dual']['lower']))
            cost['LP_FATIGUE']=cost['LP_TIME']+fat_seconds
            assert scores['CHEAP_RAY']<=time_bound['primalMultiplier']+1e-6
            scored.append({'case':feature['case'],'candidate':feature['candidate'],'seed':seed,'scores':scores,'scoringSeconds':cost,
                'lpTime':time_bound,'lpFatigue':fat_bound})
    write_once(root/stem/'predictions-before-labels.json',{'records':scored,'outcomesLoaded':False,'searchFE':0})
    return scored


def selected_indices(scores):
    values=np.asarray(scores);best=float(np.min(values))
    return np.flatnonzero(np.abs(values-best)<=1e-12*max(1.,abs(best)))


def analyze_instance(root,spec,seeds):
    stem=spec['stem'];metadata=read(root/stem/'physical-coefficients.json')
    predictions=score_inputs(root,stem,metadata,seeds) # Outcome files are intentionally first opened below.
    plan=read(root/stem/'manifest.json');case_by={r['id']:r for r in plan['cases']}
    outcomes={};receipts={};inputs={}
    for seed in seeds:
        for r in rows(root/stem/str(seed)/'probe/outcomes.jsonl'):outcomes[(r['case'],r['candidate'])]=r
        for r in rows(root/stem/str(seed)/'probe/cases-receipt.jsonl'):receipts[r['case']]=r
        for r in rows(root/stem/str(seed)/'probe/features.jsonl'):inputs[(r['case'],r['candidate'])]=r
    grouped={}
    for p in predictions:grouped.setdefault(p['case'],[]).append(p)
    cases=[];scale=spec['normalization']['scale'];lower=spec['normalization']['lower']
    for id,records in grouped.items():
        source=case_by[id];background=np.vstack([source['background'],*[p['objectives'] for p in source['teachers']]])
        base=(background-lower)/scale;hv=float(hypervolume(base,(1.5,)*3));gains=[];rays=[];eval_seconds=[]
        for p in records:
            observed=outcomes[(id,p['candidate'])];target=inputs[(id,p['candidate'])]['parentObjectives']
            point=(np.asarray(observed['objectives'])-lower)/scale
            gains.append(max(0.,float(hypervolume(np.vstack([base,point]),(1.5,)*3)-hv)))
            ray=float(np.max(np.asarray(observed['objectives'])/target));rays.append(ray)
            assert p['scores']['LP_TIME']<=ray+1e-6 and p['scores']['LP_FATIGUE']<=ray+1e-6
            eval_seconds.append(observed['evaluationSeconds'])
        best=max(gains);informative=best>1e-10;methods={}
        for method in METHODS:
            selected=np.arange(len(records)) if method=='RANDOM' else selected_indices([p['scores'][method] for p in records])
            selected_gain=float(np.mean(np.asarray(gains)[selected]));score_seconds=sum(p['scoringSeconds'].get(method,0.) for p in records)
            if method in ('GREEDY','TAIL_SUM','TAIL_RAY'):score_seconds=receipts[id]['cheapFeatureSeconds']
            rho=None
            if method!='RANDOM' and len(set(rays))>1 and len(set(p['scores'][method] for p in records))>1:
                rho=float(spearmanr([p['scores'][method] for p in records],rays).statistic)
            methods[method]={'selectedExpectedAddedHV':selected_gain,'selectedIndices':selected.tolist(),
                'regretFraction':(best-selected_gain)/best if informative else None,'scoreSeconds':score_seconds,
                'scorePlusSelectedEvaluationSeconds':score_seconds+float(np.mean(np.asarray(eval_seconds)[selected])),
                'raySpearman':rho}
        cases.append({'case':id,'seed':source['sourceSeed'],'candidateCount':len(records),'informative':informative,
            'bestAddedHV':best,'methods':methods,'allCandidateEvaluationSeconds':sum(eval_seconds),
            'constructionSeconds':receipts[id]['constructionSeconds']})
    means={m:float(np.mean([c['methods'][m]['selectedExpectedAddedHV'] for c in cases])) for m in METHODS}
    effects={candidate:{control:100*(means[candidate]/means[control]-1) if means[control]>0 else None
            for control in ('GREEDY','TAIL_SUM','TAIL_RAY','CHEAP_RAY','RANDOM','LP_TIME') if control!=candidate}
            for candidate in ('LP_TIME','LP_FATIGUE')}
    informative=sum(c['informative'] for c in cases)
    quality={m:informative>=8 and all(effects[m][c] is not None and effects[m][c]>=10 for c in ('GREEDY','TAIL_SUM','TAIL_RAY','CHEAP_RAY'))
        and effects[m]['RANDOM'] is not None and effects[m]['RANDOM']>=20 for m in ('LP_TIME','LP_FATIGUE')}
    cost={m:float(np.median([c['methods'][m]['scorePlusSelectedEvaluationSeconds']/max(1e-12,c['allCandidateEvaluationSeconds']) for c in cases])) for m in ('LP_TIME','LP_FATIGUE')}
    result={'stem':stem,'cases':cases,'informativeCases':informative,'totalCases':len(cases),'meanSelectedAddedHV':means,
        'effectsPct':effects,'qualityGate':quality,'medianScoreCostVsFullEnumeration':cost,
        'fatigueIndependentQuality':effects['LP_FATIGUE']['LP_TIME'] is not None and effects['LP_FATIGUE']['LP_TIME']>=5,
        'scope':'Same-pool, counterfactual one-evaluation selection with tie expectations. Not an online method run or closed-loop same-FE/time superiority. LP cost omits IO and is already a favorable lower accounting envelope.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs,seeds):
    result=[analyze_instance(root,s,seeds) for s in specs]
    out={'instances':[{k:v for k,v in r.items() if k!='cases'} for r in result],
        'worthGeneratorExperiment':all(r['qualityGate']['LP_TIME'] and r['medianScoreCostVsFullEnumeration']['LP_TIME']<=1 for r in result),
        'worthFatigueExperiment':all(r['qualityGate']['LP_FATIGUE'] and r['fatigueIndependentQuality'] and r['medianScoreCostVsFullEnumeration']['LP_FATIGUE']<=1 for r in result)}
    write_once(root/'analysis.json',out);return out

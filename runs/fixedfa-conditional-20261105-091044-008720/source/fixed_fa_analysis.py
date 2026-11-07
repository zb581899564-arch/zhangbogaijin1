"""Paired conditional fixed-FA effects; no claim about the original unconstrained complete algorithm."""
import numpy as np
from run_long_budget_bridge import read,rows,write_once,hypervolume,igd_plus,nondominated
from fixed_fa_execution import METHODS


def effect(a,b):return float(100*(a/b-1)) if b>1e-12 else None


def middle(values):
    valid=[v for v in values if v is not None]
    return float(np.median(valid)) if valid else None


def analyze_instance(root,spec,contexts,seeds):
    stem,norm=spec['stem'],spec['normalization'];cases=[];independent=[]
    for context in contexts:
        for seed in seeds:
            values={}
            for method in METHODS:
                path=root/stem/context['contextId']/str(seed)/method
                point=next(r for r in rows(path/'anytime.jsonl') if r['checkpointKind']=='FE' and r['checkpoint']==5100)
                assert point['reached'];values[method]=(np.asarray(point['front'])-norm['lower'])/norm['scale']
            common=nondominated(np.vstack(list(values.values())));observations={}
            for method,points in values.items():
                folder=root/stem/context['contextId']/str(seed)/method;r=rows(folder/'run-receipt.jsonl')[0]
                observations[method]={'HV':{str(ref):float(hypervolume(points,(ref,)*3)) for ref in (1.25,1.5,2.)},
                    'IGDplus':float(igd_plus(points,common)),'frontSize':len(points),'searchSeconds':r['searchSeconds'],
                    'objectiveMinRaw':(points*norm['scale']+norm['lower']).min(axis=0).tolist()}
            a,b,c=(observations[m] for m in ('FULL_FIXED','NSGA_FIXED','UNIFORM_FIXED'))
            denom=a['IGDplus']+b['IGDplus']
            cases.append({'contextId':context['contextId'],'seed':seed,'origins':sorted({s['origin'] for s in context['sources']}),
                'observations':observations,'fullVsNsgaHVPct':{str(ref):effect(a['HV'][str(ref)],b['HV'][str(ref)]) for ref in (1.25,1.5,2.)},
                'fullVsUniformHVPct':effect(a['HV']['1.5'],c['HV']['1.5']),
                'IGDplusSymmetricWorseningPct':200*(a['IGDplus']-b['IGDplus'])/denom if denom else 0.,
                'searchCostRatioVsNsga':a['searchSeconds']/b['searchSeconds']})
    hv=[c['fullVsNsgaHVPct']['1.5'] for c in cases];duty=[c['fullVsUniformHVPct'] for c in cases]
    informative=all(v is not None for v in hv+duty)
    source_effects={origin:middle([c['fullVsNsgaHVPct']['1.5'] for c in cases if origin in c['origins']]) for origin in ('FULL','NSGA')}
    sensitivity={str(ref):middle([c['fullVsNsgaHVPct'][str(ref)] for c in cases]) for ref in (1.25,2.)}
    quality=informative and middle(hv)>=.5 and sum(v>=0 for v in hv)/len(hv)>=.6
    duties=informative and middle(duty)>=1
    sources=all(v is not None and v>=-1 for v in source_effects.values())
    robust=all(v is not None and v>=0 for v in sensitivity.values())
    auxiliary=middle([c['IGDplusSymmetricWorseningPct'] for c in cases])<=5
    cost=middle([c['searchCostRatioVsNsga'] for c in cases])<=1.25
    result={'stem':stem,'uniqueContexts':len(contexts),'pairedComparisons':len(cases),'cases':cases,
        'medianFullVsNsgaHVPct':middle(hv),'nonnegativeVsNsgaPairs':sum(v is not None and v>=0 for v in hv),
        'medianFullVsUniformHVPct':middle(duty),'medianByFAOriginVsNsgaHVPct':source_effects,
        'referenceSensitivityMediansPct':sensitivity,'medianIGDplusSymmetricWorseningPct':middle([c['IGDplusSymmetricWorseningPct'] for c in cases]),
        'medianActualSearchCostRatioVsNsga':middle([c['searchCostRatioVsNsga'] for c in cases]),
        'qualityGate':bool(quality),'fourDutyGate':bool(duties),'sourceGate':bool(sources),'sensitivityGate':bool(robust),
        'auxiliaryGate':bool(auxiliary),'costGate':bool(cost),'supported':bool(quality and duties and sources and robust and auxiliary and cost),
        'limits':'FixedFA conditional global-only development test, correlated source contexts, not independent instances or a full model/algorithm comparison. No same-time, fatigue-specific, context refresh or original-author claim.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs,contexts,seeds):
    results=[analyze_instance(root,s,contexts[s['stem']],seeds) for s in specs]
    result={'instances':results,'supportsConditionalArchitecture':all(r['supported'] for r in results),
        'scope':'Prerequisite diagnostic only. Full goal, ordinary unconstrained baselines/Li, trueTIME, beta0 specificity and independent confirmation remain unachieved.'}
    write_once(root/'analysis.json',result);return result

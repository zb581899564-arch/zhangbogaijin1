"""Actual completed-by-T fronts, fixed source normalization, and prespecified development gates."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume, igd_plus, nondominated


def analyze(root):
    protocol=read(root/'protocol.json');summaries=[]
    for spec in protocol['instances']:
        stem,norm=spec['stem'],spec['normalization'];seconds=protocol['timeSeconds'][stem]
        fronts={};receipts={}
        normalized=lambda values:(np.asarray(values).reshape(-1,3)-norm['lower'])/norm['scale']
        for seed in protocol['seeds']:
            for label in protocol['methods']:
                folder=root/stem/f'{seed}-{label}'
                end=next(r for r in rows(folder/'anytime.jsonl') if r['checkpointKind']=='TIME' and r['checkpoint']==seconds)
                assert end['reached'] and end['elapsedSeconds']<=seconds
                fronts[(seed,label)]=normalized(end['front'])
                receipts[(seed,label)]=rows(folder/'run-receipt.jsonl')[0]
        empirical=nondominated(np.vstack(list(fronts.values())))
        observations=[]
        for (seed,label),front in fronts.items():
            receipt=receipts[(seed,label)]
            observations.append({'seed':seed,'method':label,'successfulFE':receipt['successful'],
                'attemptedFE':receipt['attempted'],'timeInterruptedAttempts':receipt['timeInterruptedAttempts'],
                'searchSeconds':receipt['searchSeconds'],'deadlineOvershootSeconds':max(0,receipt['searchSeconds']-seconds),
                'HV':{str(ref):float(hypervolume(front,(ref,)*3)) for ref in (1.25,1.5,2.)},
                'IGDplus':float(igd_plus(front,empirical)),
                'rawObjectiveMin':(front*norm['scale']+norm['lower']).min(axis=0).tolist()})
        indexed={(o['seed'],o['method']):o for o in observations};comparisons=[]
        for control in ('FULL_SERIAL','NSGA_ANCHOR','LI_ANCHOR','FORCE_ANCHOR'):
            effects={}
            for ref in (1.25,1.5,2.):
                values=[100*(indexed[(seed,'FULL_ANCHOR')]['HV'][str(ref)]/indexed[(seed,control)]['HV'][str(ref)]-1)
                        for seed in protocol['seeds']]
                effects[str(ref)]={'pairedPct':values,'medianPct':float(np.median(values)),
                    'wins':sum(v>0 for v in values),'atLeastMinusOnePct':sum(v>=-1 for v in values)}
            igd=[]
            for seed in protocol['seeds']:
                a=indexed[(seed,'FULL_ANCHOR')]['IGDplus'];b=indexed[(seed,control)]['IGDplus']
                igd.append(200*(a-b)/(a+b) if a+b>0 else 0.)
            comparisons.append({'control':control,'effects':effects,'IGDplusSymmetricWorseningPct':igd,
                                'medianIGDplusSymmetricWorseningPct':float(np.median(igd))})
        compared={c['control']:c for c in comparisons}
        own=compared['FULL_SERIAL']['effects']['1.5'];classic=compared['NSGA_ANCHOR']['effects']['1.5']
        cost_quality=own['medianPct']>=1 and own['wins']>=2
        competitiveness=classic['medianPct']>=-1 and classic['atLeastMinusOnePct']>=2
        baselines=all(compared[c]['effects']['1.5']['medianPct']>=0 and compared[c]['effects']['1.5']['wins']>=2
                      for c in ('LI_ANCHOR','FORCE_ANCHOR'))
        sensitivity=all(compared[c]['effects'][str(ref)]['medianPct']>=( -2 if c=='NSGA_ANCHOR' else 0)
                        for c in compared for ref in (1.25,2.))
        auxiliary=all(c['medianIGDplusSymmetricWorseningPct']<=5 for c in comparisons)
        item={'stem':stem,'seconds':seconds,'observations':observations,'comparisons':comparisons,
              'ownTimeQualityGate':bool(cost_quality),'classicGate':bool(competitiveness),
              'baselineGate':bool(baselines),'referenceSensitivityGate':bool(sensitivity),'auxiliaryGate':bool(auxiliary),
              'primaryDevelopmentGate':bool(cost_quality and competitiveness and baselines and sensitivity and auxiliary)}
        write_once(root/stem/'analysis.json',item);summaries.append(item)
    result={'instances':[{k:v for k,v in r.items() if k!='observations'} for r in summaries],
        'worthSeparateMechanismConfirmation':all(r['primaryDevelopmentGate'] for r in summaries),
        'scope':'ActualTIME_LIMIT, two reused development instances and three new search seeds. Same-FE physics/search '
                'semantics are unchanged by the engineering kernel. A pass would still require role/sharing ablations, '
                'held-out instances, paper novelty and reproducibility; no automatic goal completion.'}
    write_once(root/'analysis.json',result)
    return result

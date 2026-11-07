"""Predeclared paired complete-algorithm capability gates; existing normalization, no search feedback."""
import numpy as np
from run_long_budget_bridge import read,rows,write_once,hypervolume,igd_plus,nondominated
from pa_capability_support import ARMS


def at(root,stem,seed,phase,arm,endpoint):
    folder=root/stem/str(seed)/(phase+'-'+arm)
    kind='TIME' if phase=='TIME' else 'FE'
    point,=[p for p in rows(folder/'anytime.jsonl') if p['checkpointKind']==kind and p['checkpoint']==endpoint and p['reached']]
    return folder,point


def analyze(root,phase):
    plan=read(root/'protocol.json');instances=[]
    for spec in plan['instances']:
        stem=spec['stem'];endpoint=spec['time_seconds'] if phase=='TIME' else plan['fe100k'] if phase=='FE100K' else plan['fe500k']
        norm=spec['normalization'];normalize=lambda x:(np.asarray(x,float).reshape(-1,3)-norm['lower'])/norm['scale']
        fronts={};observations=[]
        for seed in plan['seeds']:
            for arm in ARMS:
                folder,point=at(root,stem,seed,phase,arm,endpoint);fronts[seed,arm]=normalize(point['front'])
        reference=nondominated(np.vstack(list(fronts.values())))
        for (seed,arm),front in fronts.items():
            folder,point=at(root,stem,seed,phase,arm,endpoint);receipt,=rows(folder/'run-receipt.jsonl')
            observations.append({'seed':seed,'arm':arm,'frontSize':len(front),
                'HV':{str(r):hypervolume(front,(r,)*3) for r in (1.25,1.5,2.)},'IGDplus':igd_plus(front,reference),
                'objectiveMin':(front*norm['scale']+norm['lower']).min(axis=0).tolist(),
                'successfulFE':receipt['successful'],'attemptedFE':receipt['attempted'],'searchSeconds':receipt['searchSeconds'],
                'stageFE':{s:receipt['search'].get(s+'.evaluations',0) for s in ('initialization','global','inter','intra')},
                'completeGenerations':receipt['search'].get('completeGenerations',receipt['search'].get('generations')),
                'checkpointFE':point['fe'],'checkpointSeconds':point['elapsedSeconds']})
        index={(r['seed'],r['arm']):r for r in observations};comparisons=[]
        for control in ARMS[1:]:
            pairs=[]
            for seed in plan['seeds']:
                a,b=index[seed,'PA_JOINT'],index[seed,control];den=a['IGDplus']+b['IGDplus']
                assert all(b['HV'][str(r)]>1e-12 for r in (1.25,1.5,2.))
                pairs.append({'seed':seed,'HVEffectPct':{str(r):100*(a['HV'][str(r)]/b['HV'][str(r)]-1) for r in (1.25,1.5,2.)},
                    'IGDplusSymmetricWorseningPct':200*(a['IGDplus']-b['IGDplus'])/den if den else 0.})
            med={str(r):float(np.median([p['HVEffectPct'][str(r)] for p in pairs])) for r in (1.25,1.5,2.)}
            auxiliary=float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs]))
            comparisons.append({'control':control,'pairs':pairs,'medianHVEffectPct':med,'medianIGDplusSymmetricWorseningPct':auxiliary,
                'nonnegativeEverySeed':all(p['HVEffectPct']['1.5']>=-1e-10 for p in pairs),
                'referenceDirectionStable':all(med[str(r)]>=-1e-10 for r in (1.25,2.)),
                'auxiliaryPass':auxiliary<=5.})
        by={c['control']:c for c in comparisons}
        learned=by['PA_RELABEL'];plain=by['NSGA2_PLAIN']
        learning=learned['medianHVEffectPct']['1.5']>=1-1e-10 and learned['nonnegativeEverySeed'] and learned['referenceDirectionStable']
        global_pass=plain['medianHVEffectPct']['1.5']>=-1e-10 and plain['auxiliaryPass']
        strong=all(by[c]['medianHVEffectPct']['1.5']>=1-1e-10 and by[c]['nonnegativeEverySeed']
            and by[c]['referenceDirectionStable'] and by[c]['auxiliaryPass'] for c in ('NSGA2_DEEP','FULL_SHARED_DEEP','LI_RECON_DEEP'))
        instances.append({'stem':stem,'phase':phase,'observations':observations,'comparisons':comparisons,
            'learningGate':bool(learning),'ordinaryGlobalGate':bool(global_pass),'strongControlGate':bool(strong)})
    result={'phase':phase,'instances':instances,'learningGate':all(x['learningGate'] for x in instances),
        'ordinaryGlobalGate':all(x['ordinaryGlobalGate'] for x in instances),'strongControlGate':all(x['strongControlGate'] for x in instances),
        'goalAchieved':False,'scope':'Two reused developmentinstances and2freshseeds; complete unaugmented ordinary method, no novelty/confirmation claim'}
    result['capabilityGate']=result['learningGate'] and result['ordinaryGlobalGate']
    write_once(root/(phase.lower()+'-analysis.json'),result);return result

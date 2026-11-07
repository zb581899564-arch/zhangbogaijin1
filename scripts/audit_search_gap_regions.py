"""Post-hoc objective-region diagnosis of existing complete searches; no evaluator or new candidate."""
from datetime import datetime
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,hypervolume,nondominated

SOURCE=ROOT/'runs/makespan-tie-screen-20261105-025223-471920'
ARMS=('STRICT_FULL','NSGA_STRICT')


def hv(points,upper=1.5):
    return float(hypervolume(points,(upper,1.5,1.5)))


def analyze_instance(spec,seeds):
    stem=spec['stem'];norm=spec['normalization']
    normalized=lambda points:(np.asarray(points)-norm['lower'])/norm['scale']
    curves={(seed,arm):{r['fe']:normalized(r['front']) for r in rows(SOURCE/stem/str(seed)/arm/'anytime.jsonl')}
            for seed in seeds for arm in ARMS}
    final={k:v[500000] for k,v in curves.items()}
    common=nondominated(np.vstack(list(final.values())))
    cuts=[0.,*map(float,np.quantile(common[:,0],[.25,.5,.75])),1.5]
    assert cuts==sorted(cuts)
    regional=[]
    for seed in seeds:
        parts=[]
        for lo,hi in zip(cuts,cuts[1:]):
            volumes={a:hv(final[(seed,a)],hi)-hv(final[(seed,a)],lo) for a in ARMS}
            parts.append({'lowerCmaxNormalized':lo,'upperCmaxNormalized':hi,'HV':volumes,
                          'nsgaMinusMain':volumes['NSGA_STRICT']-volumes['STRICT_FULL']})
        deficit=hv(final[(seed,'NSGA_STRICT')])-hv(final[(seed,'STRICT_FULL')])
        assert abs(sum(p['nsgaMinusMain'] for p in parts)-deficit)<1e-11
        regional.append({'seed':seed,'parts':parts,'nsgaMinusMain':deficit,
            'firstRegionShareOfSignedDeficit':parts[0]['nsgaMinusMain']/deficit if deficit>1e-10 else None})
    checkpoints=[]
    for fe in curves[(seeds[0],ARMS[0])]:
        effects=[];minimums=[]
        for seed in seeds:
            main,nsga=(curves[(seed,a)][fe] for a in ARMS)
            effects.append(100*(hv(main)/hv(nsga)-1))
            minimums.append((100*(main.min(axis=0)/nsga.min(axis=0)-1)).tolist())
        checkpoints.append({'FE':fe,'mainVsNsgaHVPct':effects,'mainVsNsgaMedianHVPct':float(np.median(effects)),
            'mainVsNsgaObjectiveMinimumPct':minimums,'medianObjectiveMinimumPct':np.median(minimums,axis=0).tolist()})
    return {'stem':stem,'empiricalCommonCmaxCuts':cuts,'regionalDeficits':regional,'checkpoints':checkpoints,
        'medianFirstRegionShareAmongPositiveDeficitSeeds':float(np.median([r['firstRegionShareOfSignedDeficit'] for r in regional if r['firstRegionShareOfSignedDeficit'] is not None]))
            if any(r['firstRegionShareOfSignedDeficit'] is not None for r in regional) else None}


def main():
    root=ROOT/'runs'/datetime.now().strftime('search-gap-regions-%Y%m%d-%H%M%S-%f');root.mkdir()
    p=read(SOURCE/'protocol.json')
    write_once(root/'protocol.json',{'source':str(SOURCE),'arms':ARMS,'seeds':p['seeds'],'instances':p['instances'],
        'scope':'Explicitly post-hoc explanation of already-complete development results, not a new candidate gate, independent test or statistical significance claim.',
        'regions':'Use per-instance quartiles of Cmax in the pooled empirical ND union from both methods and all three final seeds. Integrate3D HV over four disjoint Cmax slabs. Report signed contributions; do not sum medians or hide offsetting regions.',
        'checkpoints':'All saved common FE checkpoints and per-objective minima; lower minima are not alone a multiobjective performance conclusion.',
        'cost':'Zero search FE, zero decoder calls, no new genome or online scoring. Physical FA/resource/order causes are not inferred from objective regions alone.'})
    result={'instances':[analyze_instance(s,p['seeds']) for s in p['instances']],'searchFE':0,'decoderCalls':0}
    write_once(root/'analysis.json',result)
    print('SEARCH_GAP_REGIONS_ROOT',root,flush=True)
    for r in result['instances']:
        print(r['stem'],'checkpoints',[(v['FE'],v['mainVsNsgaMedianHVPct'],v['medianObjectiveMinimumPct']) for v in r['checkpoints']],
            'firstRegionShares',[v['firstRegionShareOfSignedDeficit'] for v in r['regionalDeficits']],flush=True)


if __name__=='__main__':main()

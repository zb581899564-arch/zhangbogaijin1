"""Fixed-donor-source comparison, with recipient/context clusters and actual scoring costs."""
from collections import Counter
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume

METHODS=('WITHIN','SHARED','RANDOM_SHARED','INITIAL_SHARED')


def analyze_instance(root,spec):
    stem,norm=spec['stem'],spec['normalization'];contexts=read(root/stem/'contexts.json')
    records=rows(root/stem/'probe/outcomes.jsonl');batches=rows(root/stem/'probe/batch-costs.jsonl')
    normal=lambda p:(np.asarray(p,dtype=float).reshape(-1,3)-norm['lower'])/norm['scale']
    cells=[];errors=[];context_reports=[]
    for context in contexts:
        id=context['contextId'];background=normal(context['background']);scorer=UncoveredVolume(background,(1.5,)*3)
        baseline=hypervolume(background,(1.5,)*3);assert abs(baseline-scorer.background_hv)<1e-11
        known=context['current']+context['initial'];assert np.max(scorer.gains(normal([p['objectives'] for p in known])))<1e-10
        selected=[r for r in records if r['context']==id];assert len(selected)==4*16*8
        for r in selected:
            donor=(context['initial'] if r['method']=='INITIAL_SHARED' else
                   [p for p in context['current'] if p['role']=='CENTER'] if r['method']=='WITHIN' else context['current'])[r['donorIndex']]
            assert r['donorRole']==donor['role']
            assert donor['earliestKnownPaidFE']<=context['preBatchFE']
        for recipient in range(8):
            values={};all_gains=[]
            for method in METHODS:
                own=[r for r in selected if r['recipient']==recipient and r['method']==method]
                assert {r['rep'] for r in own}==set(range(16))
                costs={(b['rep'],b['method']):b['scoreSeconds']/b['offspring'] for b in batches if b['context']==id}
                gain=scorer.gains(normal([r['objectives'] for r in own]));all_gains.extend(gain)
                values[method]={'meanSingleAddedHV':float(np.mean(gain)),
                    'meanCallSeconds':float(np.mean([costs[(r['rep'],method)]+r['drawSeconds']+r['generationSeconds']+r['evaluationSeconds'] for r in own])),
                    'donorRoleCounts':dict(Counter(r['donorRole'] for r in own))}
            cells.append({'context':id,'seed':context['seed'],'step':context['step'],'recipient':recipient,
                          'informative':bool(max(all_gains)>1e-10),'methods':values})
        for r in (selected[0],selected[-1]):
            point=normal([r['objectives']]);difference=hypervolume(np.vstack([background,point]),(1.5,)*3)-baseline
            error=float(abs(scorer.gains(point)[0]-difference));assert error<1e-11;errors.append(error)
        context_reports.append({'context':id,'seed':context['seed'],'step':context['step'],'preBatchFE':context['preBatchFE'],
            'backgroundHV':baseline,'sharedDonorRoles':dict(Counter(r['donorRole'] for r in selected if r['method']=='SHARED'))})
    assert len(cells)==48
    means={m:float(np.mean([c['methods'][m]['meanSingleAddedHV'] for c in cells])) for m in METHODS}
    effects={m:100*(means['SHARED']/means[m]-1) if means[m]>1e-12 else None for m in METHODS if m!='SHARED'}
    grouped=[]
    for key in ('seed','step'):
        for value in sorted({c[key] for c in cells}):
            subset=[c for c in cells if c[key]==value]
            grouped.append({'key':key,'value':value,**{m:float(np.mean([c['methods'][m]['meanSingleAddedHV'] for c in subset])) for m in METHODS}})
    wins=sum(c['methods']['SHARED']['meanSingleAddedHV']>c['methods']['WITHIN']['meanSingleAddedHV']+1e-12 for c in cells)
    informative=sum(c['informative'] for c in cells)
    ratio=float(np.median([c['methods']['SHARED']['meanCallSeconds']/c['methods']['WITHIN']['meanCallSeconds'] for c in cells]))
    quality=informative>=24 and wins>=27 and all(effects[m] is not None and effects[m]>=threshold for m,threshold in
        (('WITHIN',10),('INITIAL_SHARED',10),('RANDOM_SHARED',5))) and all(
        g['SHARED']>g['WITHIN'] if g['key']=='seed' else g['SHARED']>=g['WITHIN'] for g in grouped)
    result={'stem':stem,'cells':cells,'contexts':context_reports,'informativeParents':informative,'totalParents':len(cells),
        'candidateWinsVsWithin':wins,'meanSingleAddedHV':means,'candidateEffectsPct':effects,'groupedMeans':grouped,
        'medianCallCostVsWithin':ratio,'qualityGate':bool(quality),'necessaryCostGate':bool(ratio<=1.25),
        'independentHVCheckMaxError':max(errors),
        'scope':'Reused source seeds, exact pre-batch archive. New offspring and same fixed recipient; only free parents. '
                'No whole-loop, same-time, four-role specificity or novelty conclusion. Score costs actually recomputed per8-child batch.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs):
    results=[analyze_instance(root,s) for s in specs]
    result={'instances':[{k:v for k,v in r.items() if k not in ('cells','contexts')} for r in results],
            'worthFreshClosedLoop':all(r['qualityGate'] and r['necessaryCostGate'] for r in results)}
    write_once(root/'analysis.json',result);return result

"""Same-parent single-offspring value across a fixed complete direction set, clustered by actual parent."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume

METHODS=('OLDEST','CURRENT','RANDOM','DIR_SUM','BALANCED','DIR_CHEBY')


def analyze_instance(root,spec):
    stem,norm=spec['stem'],spec['normalization'];cases=read(root/stem/'cases.json')
    records=rows(root/stem/'probe/outcomes.jsonl');indexed={}
    for r in records:indexed.setdefault(r['case'],[]).append(r)
    normalized=lambda p:(np.asarray(p).reshape(-1,3)-norm['lower'])/norm['scale']
    cells=[];independent_errors=[]
    for case in cases:
        source=case['source'];background=normalized(source['background']);scorer=UncoveredVolume(background,(1.5,)*3)
        baseline=hypervolume(background,(1.5,)*3);assert abs(scorer.background_hv-baseline)<1e-11
        known=[source[k]['objectives'] for k in ('parent','personal','global')]+[h['objectives'] for h in source['history']]
        assert np.max(scorer.gains(normalized(known)))<1e-10,'Known source earned unearned novelty'
        selected=indexed[case['caseId']];assert len(selected)==55*2*len(METHODS)
        methods={};all_gains=[]
        for method in METHODS:
            records_=[r for r in selected if r['method']==method]
            assert {(r['weight'],r['rep']) for r in records_}=={(w,r) for w in range(55) for r in range(2)}
            gains=scorer.gains(normalized([r['objectives'] for r in records_]));all_gains.extend(gains)
            methods[method]={'meanSingleAddedHV':float(np.mean(gains)),
                'meanAddedHVPctOfBackground':100*float(np.mean(gains))/baseline,
                'meanSelectorKernelEvaluationSeconds':float(np.mean([r['selectionSeconds']+r['generationSeconds']+r['evaluationSeconds'] for r in records_])),
                'changedOldestFraction':float(np.mean([r['chosenHistoryIndex']!=0 for r in records_])),
                'chosenHistoryIndices':sorted({r['chosenHistoryIndex'] for r in records_})}
        for record in (selected[0],selected[-1]):
            point=normalized([record['objectives']]);old=hypervolume(np.vstack([background,point]),(1.5,)*3)-baseline
            error=abs(scorer.gains(point)[0]-old);assert error<1e-11;independent_errors.append(error)
        cells.append({'case':case['caseId'],'sourceSeed':case['seed'],'historySize':len(source['history']),
            'informative':max(all_gains)>1e-10,'methods':methods})
    means={m:float(np.mean([c['methods'][m]['meanSingleAddedHV'] for c in cells])) for m in METHODS}
    effect={m:100*(means['DIR_CHEBY']/means[m]-1) if means[m]>1e-12 else None for m in METHODS if m!='DIR_CHEBY'}
    seed_positive=[]
    for seed in sorted({c['sourceSeed'] for c in cells}):
        selected=[c for c in cells if c['sourceSeed']==seed]
        seed_positive.append({'seed':seed,'candidateMean':float(np.mean([c['methods']['DIR_CHEBY']['meanSingleAddedHV'] for c in selected])),
                              'oldestMean':float(np.mean([c['methods']['OLDEST']['meanSingleAddedHV'] for c in selected]))})
    wins=sum(c['methods']['DIR_CHEBY']['meanSingleAddedHV']>c['methods']['OLDEST']['meanSingleAddedHV']+1e-12 for c in cells)
    informative=sum(c['informative'] for c in cells)
    cost=float(np.median([c['methods']['DIR_CHEBY']['meanSelectorKernelEvaluationSeconds']/
                          c['methods']['OLDEST']['meanSelectorKernelEvaluationSeconds'] for c in cells]))
    quality=informative>=8 and wins>=9 and effect['OLDEST'] is not None and effect['OLDEST']>=10 \
        and all(effect[m] is not None and effect[m]>=5 for m in ('CURRENT','RANDOM','DIR_SUM','BALANCED')) \
        and all(s['candidateMean']>s['oldestMean'] for s in seed_positive)
    result={'stem':stem,'cells':cells,'totalParents':len(cells),'informativeParents':informative,
        'candidateWinsVsOldest':wins,'meanSingleAddedHV':means,'candidateEffectsPct':effect,'sourceSeedMeans':seed_positive,
        'qualityGate':bool(quality),'medianCallCostVsOldest':cost,'necessaryCostGate':cost<=1.10,
        'independentHVCheckMaxError':max(independent_errors),
        'scope':'Reused development contexts;55 fixed directions and2 construction samples per actual parent. '
                'Directions are not independent instances or tuning trials. All offspring equally averaged; no per-parent '
                'direction selection. Call timings interleave shared probe archive and offline QA, not same-time method runs.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs):
    result=[analyze_instance(root,s) for s in specs]
    out={'instances':[{k:v for k,v in r.items() if k!='cells'} for r in result],
        'worthFreshClosedLoop':all(r['qualityGate'] and r['necessaryCostGate'] for r in result)}
    write_once(root/'analysis.json',out);return out

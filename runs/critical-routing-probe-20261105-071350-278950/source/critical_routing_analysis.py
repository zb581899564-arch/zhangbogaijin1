"""Compare matched finite VNS tasks, including all paid discoveries against the real old archive."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume

MODES=('FROZEN','RANDOM','CRITICAL')


def analyze_instance(root,spec):
    stem,norm=spec['stem'],spec['normalization'];cases=read(root/stem/'cases.json');records=rows(root/stem/'probe/outcomes.jsonl')
    normal=lambda p:(np.asarray(p,dtype=float).reshape(-1,3)-norm['lower'])/norm['scale']
    cells=[];errors=[]
    for case in cases:
        own=[r for r in records if r['case']==case['caseId']];assert len(own)==6
        before=np.asarray(case['parent']['objectives']);background=normal(case['background']);base=UncoveredVolume(background,(1.5,)*3).background_hv
        assert max(UncoveredVolume(background,(1.5,)*3).gains(normal([before])))<1e-10
        methods={}
        for mode in MODES:
            selected=[r for r in own if r['mode']==mode];assert {r['rep'] for r in selected}=={0,1}
            gains={str(ref):[] for ref in (1.25,1.5,2.0)};improvements=[]
            for r in selected:
                assert r['successfulFE']==257 and r['failedFE']==0 and len(r['paid'])==257
                assert r['paid'][0]=={k:case['parent'][k] for k in ('JS','FA','MA','WA','objectives')}
                points=normal([p['objectives'] for p in r['paid']]);minimum=min(p['objectives'][0] for p in r['paid'])
                assert r['returned']['objectives'][0]==minimum<=before[0]
                if mode=='FROZEN' and case['impossible']:
                    assert minimum==before[0], 'Frozen noncritical task lowered globalCmax'
                improvements.append(100*(before[0]-minimum)/before[0])
                for ref in (1.25,1.5,2.0):
                    v=UncoveredVolume(np.vstack([background,points]),(ref,)*3).background_hv-UncoveredVolume(background,(ref,)*3).background_hv
                    assert v>=-1e-11;gains[str(ref)].append(max(0.,float(v)))
                    if case['caseId']=='c0':
                        slow=hypervolume(np.vstack([background,points]),(ref,)*3)-hypervolume(background,(ref,)*3)
                        error=abs(v-slow);assert error<1e-11;errors.append(float(error))
            methods[mode]={'meanAddedHV':{ref:float(np.mean(value)) for ref,value in gains.items()},
                'meanAddedHVPctOfBackground':100*float(np.mean(gains['1.5']))/base,
                'meanMakespanImprovementPct':float(np.mean(improvements)),
                'meanMeasuredRunSeconds':float(np.mean([r['measuredRunSeconds'] for r in selected])),
                'meanVnsCalls':float(np.mean([r['routing']['vnsCalls'] for r in selected])),
                'meanFactorySwitches':float(np.mean([r['routing']['factorySwitches'] for r in selected]))}
        cells.append({'case':case['caseId'],'sourceMethod':case['sourceMethod'],'sourceVisit':case['sourceVisit'],
                      'frozenFactory':case['factory'],'impossible':case['impossible'],'backgroundHV':base,'methods':methods})
    groups=[]
    for source in sorted({c['sourceMethod'] for c in cases}):
        own=[c for c in cells if c['sourceMethod']==source];assert len(own)==8
        means={m:float(np.mean([c['methods'][m]['meanAddedHV']['1.5'] for c in own])) for m in MODES}
        cmax={m:float(np.mean([c['methods'][m]['meanMakespanImprovementPct'] for c in own])) for m in MODES}
        material=float(np.mean([c['methods']['CRITICAL']['meanAddedHVPctOfBackground'] for c in own]))
        wins=sum(c['methods']['CRITICAL']['meanAddedHV']['1.5']>c['methods']['RANDOM']['meanAddedHV']['1.5']+1e-12 for c in own)
        informative=sum(any(c['methods'][m]['meanAddedHV']['1.5']>1e-10 for m in MODES) for c in own)
        cost=float(np.median([c['methods']['CRITICAL']['meanMeasuredRunSeconds']/c['methods']['RANDOM']['meanMeasuredRunSeconds'] for c in own]))
        sensitivity=[]
        for ref in ('1.25','2.0'):
            values={m:float(np.mean([c['methods'][m]['meanAddedHV'][ref] for c in own])) for m in MODES}
            sensitivity.append({'reference':ref,'means':values,'candidatePositiveVsBoth':all(values['CRITICAL']>values[m] for m in ('FROZEN','RANDOM'))})
        quality=informative>=4 and wins>=5 and material>=.1 and means['CRITICAL']>1e-10 \
            and all(means['CRITICAL']>=1.10*means[m] and cmax['CRITICAL']>=cmax[m] for m in ('FROZEN','RANDOM')) \
            and all(s['candidatePositiveVsBoth'] for s in sensitivity)
        groups.append({'sourceMethod':source,'parents':8,'informativeParents':informative,'candidateWinsVsRandom':wins,
            'meanAddedHV':means,'meanMakespanImprovementPct':cmax,'candidateMeanAddedHVPctOfBackground':material,
            'candidateEffectsPct':{m:100*(means['CRITICAL']/means[m]-1) if means[m]>1e-12 else None for m in ('FROZEN','RANDOM')},
            'sensitivity':sensitivity,'qualityGate':bool(quality),'medianRunCostVsRandom':cost,'necessaryCostGate':bool(cost<=1.10)})
    result={'stem':stem,'cells':cells,'groups':groups,'independentHVCheckMaxError':max(errors),
        'worthMatchedClosedLoop':all(g['qualityGate'] and g['necessaryCostGate'] for g in groups),
        'limits':'Free M parents, olddevelopmenttrace,2paired samples. ActualVNS unchanged except method visibility. '
                 'Finite256FEtask and recorded costs are not whole-method TIME_LIMIT, four-role-specific benefit or independent confirmation.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs):
    results=[analyze_instance(root,s) for s in specs]
    result={'instances':[{k:v for k,v in r.items() if k!='cells'} for r in results],
            'worthMatchedClosedLoop':all(r['worthMatchedClosedLoop'] for r in results)}
    write_once(root/'analysis.json',result);return result

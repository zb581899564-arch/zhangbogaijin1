"""Conditional union-HV per paid path, clustered by original recipient, never by path step."""
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume
from research.composition_oracle.volume import UncoveredVolume

METHODS=('COVER_PATH','REPAIR_PATH','RANDOM_PATH','CLASSIC')
REFERENCES=(1.25,1.5,2.0)


def analyze_instance(root,spec):
    stem,norm=spec['stem'],spec['normalization'];n=int(stem.split('_')[0])
    pairs=read(root/stem/'pairs.json');contexts={c['contextId']:c for c in read(root/stem/'contexts.json')}
    indexed={};setups={}
    for record in rows(root/stem/'probe/outcomes.jsonl'):indexed.setdefault(record['pair'],[]).append(record)
    for record in rows(root/stem/'probe/setup-costs.jsonl'):setups[(record['pair'],record['method'])]=record['setupSeconds']
    normalized=lambda values:(np.asarray(values,dtype=float).reshape(-1,3)-norm['lower'])/norm['scale']
    pair_results=[];independent_errors=[]
    for pair in pairs:
        id=pair['pairId'];context=contexts[pair['contextId']];background=normalized(context['background'])
        scorer=UncoveredVolume(background,(1.5,)*3)
        assert np.max(scorer.gains(normalized([pair['parent']['objectives'],pair['teacher']['objectives']])))<1e-10
        selected=indexed[id];assert len(selected)==4*n
        values={}
        for method in METHODS:
            own=sorted((r for r in selected if r['method']==method),key=lambda r:r['step'])
            assert [r['step'] for r in own]==list(range(n))
            points=normalized([r['objectives'] for r in own]);gains={}
            for reference in REFERENCES:
                ref=(reference,)*3;base=UncoveredVolume(background,ref).background_hv
                joint=UncoveredVolume(np.vstack([background,points]),ref).background_hv;gain=joint-base
                assert gain>=-1e-11;gains[str(reference)]=max(0.,float(gain))
                if id=='p0':
                    expected=hypervolume(np.vstack([background,points]),ref)-hypervolume(background,ref)
                    error=float(abs(expected-gain));assert error<1e-11;independent_errors.append(error)
            if method!='CLASSIC':
                assert own[-1]['child']=={k:pair['teacher'][k] for k in ('JS','FA','MA','WA','objectives')}
            if method in ('COVER_PATH','RANDOM_PATH'):
                assert all(r['repairEdits']==r['committedViolations']==r['endpointRestorationEdits']==0 for r in own)
            values[method]={'unionAddedHV':gains,'callSeconds':setups[(id,method)]+sum(r['generationSeconds']+r['evaluationSeconds'] for r in own),
                'extraCoverJobs':sum(r['extraCoverJobs'] for r in own),'repairEdits':sum(r['repairEdits'] for r in own),
                'committedViolationSteps':sum(r['committedViolations']>0 for r in own),
                'endpointRestorationEdits':sum(r['endpointRestorationEdits'] for r in own),
                'sameAsPrevious':sum(r['sameAsPrevious'] for r in own)}
        pair_results.append({'pair':id,'context':pair['contextId'],'seed':pair['seed'],'step':pair['step'],
                             'recipient':pair['recipient'],'teacherRole':pair['teacherRole'],'methods':values})
    cells=[]
    for context in contexts.values():
        for recipient in range(8):
            selected=[p for p in pair_results if p['context']==context['contextId'] and p['recipient']==recipient]
            assert {p['teacherRole'] for p in selected}=={'MAKESPAN','ENERGY','WORKER_COST'}
            methods={m:{'meanUnionAddedHV':{str(ref):float(np.mean([p['methods'][m]['unionAddedHV'][str(ref)] for p in selected])) for ref in REFERENCES},
                        'meanCallSeconds':float(np.mean([p['methods'][m]['callSeconds'] for p in selected]))} for m in METHODS}
            cells.append({'context':context['contextId'],'seed':context['seed'],'step':context['step'],'recipient':recipient,'methods':methods,
                          'informative':any(methods[m]['meanUnionAddedHV']['1.5']>1e-10 for m in METHODS)})
    assert len(cells)==48
    means={m:float(np.mean([c['methods'][m]['meanUnionAddedHV']['1.5'] for c in cells])) for m in METHODS}
    effects={m:100*(means['COVER_PATH']/means[m]-1) if means[m]>1e-12 else None for m in METHODS if m!='COVER_PATH'}
    wins={m:sum(c['methods']['COVER_PATH']['meanUnionAddedHV']['1.5']>c['methods'][m]['meanUnionAddedHV']['1.5']+1e-12 for c in cells)
          for m in ('CLASSIC','RANDOM_PATH')}
    groups=[]
    for key in ('seed','step'):
        for value in sorted({c[key] for c in cells}):
            own=[c for c in cells if c[key]==value]
            groups.append({'key':key,'value':value,**{m:float(np.mean([c['methods'][m]['meanUnionAddedHV']['1.5'] for c in own])) for m in METHODS}})
    sensitivity=[]
    for ref in (1.25,2.0):
        values={m:float(np.mean([c['methods'][m]['meanUnionAddedHV'][str(ref)] for c in cells])) for m in METHODS}
        sensitivity.append({'reference':ref,'means':values,'positiveVsClassicAndRandom':values['COVER_PATH']>values['CLASSIC'] and values['COVER_PATH']>values['RANDOM_PATH']})
    informative=sum(c['informative'] for c in cells)
    quality=informative>=24 and wins['CLASSIC']>=27 and wins['RANDOM_PATH']>=27 and all(
        effects[m] is not None and effects[m]>=threshold for m,threshold in (('CLASSIC',10),('RANDOM_PATH',5),('REPAIR_PATH',-1))) \
        and all(g['COVER_PATH']>g['CLASSIC'] and g['COVER_PATH']>g['RANDOM_PATH'] for g in groups if g['key']=='seed') \
        and all(g['COVER_PATH']>=g['CLASSIC'] for g in groups if g['key']=='step') \
        and all(s['positiveVsClassicAndRandom'] for s in sensitivity)
    ratio=float(np.median([c['methods']['COVER_PATH']['meanCallSeconds']/c['methods']['CLASSIC']['meanCallSeconds'] for c in cells]))
    result={'stem':stem,'pairs':pair_results,'cells':cells,'totalParents':len(cells),'informativeParents':informative,'candidateWins':wins,
        'meanUnionAddedHV':means,'candidateEffectsPct':effects,'groupedMeans':groups,'sensitivity':sensitivity,
        'qualityGate':bool(quality),'medianCallCostVsClassic':ratio,'necessaryCostGate':bool(ratio<=1.25),
        'independentHVCheckMaxError':max(independent_errors),
        'limits':'Known endpoints already in pre-batch paid archive. Per-method N evaluated intermediates scored jointly; '
                 'cluster by48recipients, not144pairs or20/100steps. Ordinary path-relinking preflight, no role specificity, '
                 'fatigue specificity, whole algorithm, novelty or same-time conclusion.'}
    write_once(root/stem/'analysis.json',result);return result


def analyze(root,specs):
    results=[analyze_instance(root,s) for s in specs]
    result={'instances':[{k:v for k,v in r.items() if k not in ('pairs','cells')} for r in results],
            'worthFreshClosedLoop':all(r['qualityGate'] and r['necessaryCostGate'] for r in results)}
    write_once(root/'analysis.json',result);return result

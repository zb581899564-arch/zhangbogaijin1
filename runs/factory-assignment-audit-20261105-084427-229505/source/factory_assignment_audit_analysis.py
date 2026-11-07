"""Observed FE coverage and sequential archive credit; never interpreted as isolated causal FA gain."""
import numpy as np
from run_long_budget_bridge import rows,read,write_once,hypervolume
from fa_admission_volume import volume,checks


def analyze_case(out,stem,method,norm):
    audit=rows(out/'fa-audit.jsonl')[0];receipt=rows(out/'run-receipt.jsonl')[0]
    assert audit['status']=='PASS' and audit['successfulFE']==receipt['successful']==500000
    assert audit['unknownParentHints']==audit['protectedActualFAChanges']==0
    counters=audit['counters'];assert sum(v['successfulFE'] for v in counters.values())==500000
    for phase in ('initialization','global','inter','intra'):
        assert sum(v['successfulFE'] for k,v in counters.items() if k.split('/')[0]==phase)==receipt['search'].get(phase+'.evaluations',0)
    accepted=rows(out/'fa-inter-acceptances.jsonl')
    assert len(accepted)==audit['interAcceptanceEvents']==receipt['search'].get('inter.accepted',0)
    assert all(r['stage']=='inter' and r['parentHintPaidFE']<r['fe'] for r in accepted)
    admissions=rows(out/'fa-admissions.jsonl');assert len(admissions)==audit['admissionEvents']==sum(v.get('admissions',0) for v in counters.values())
    front=np.empty((0,3));previous_hv=0.;credit={};trace=[];independent_checks=[]
    checkpoints={r['checkpoint']:r for r in rows(out/'anytime.jsonl') if r['checkpointKind']=='FE' and r['reached']}
    initial_hv=None
    for ordinal,event in enumerate(admissions):
        point=np.asarray(event['objectives'],dtype=float)
        assert event['parentHintPaidFE']<event['fe'] and (ordinal==0 or event['fe']>admissions[ordinal-1]['fe'])
        assert not len(front) or not np.any(np.all(front<=point,axis=1))
        if len(front):front=front[~np.all(point<=front,axis=1)]
        front=np.vstack([front,point]);normalized=(front-norm['lower'])/norm['scale'];after=volume(normalized)
        assert after>=previous_hv-1e-11;gain=max(0.,after-previous_hv)
        key='/'.join([event['stage'],event['role'],'PROTECTED' if event['protectedFamily'] else 'FREE',
                      'INITIAL' if event['changedJobs']<0 else 'FA_CHANGED' if event['changedJobs']>0 else 'FA_SAME'])
        credit[key]=credit.get(key,0.)+gain
        trace.append({'fe':event['fe'],'key':key,'changedJobs':event['changedJobs'],'novelFA':event['novelFA'],
                      'archiveHV':after,'sequentialHVIncrement':gain})
        if ordinal%257==0 and len(independent_checks)<16:
            error=abs(after-hypervolume(normalized,(1.5,)*3));assert error<1e-11
            independent_checks.append({'admissionOrdinal':ordinal,'frontSize':len(front),'maxAbsoluteError':error})
        previous_hv=after
    assert abs(sum(credit.values())-previous_hv)<1e-9
    for fe,saved in checkpoints.items():
        known=[event['objectives'] for event in admissions if event['fe']<=fe]
        a=np.asarray(known,dtype=float).reshape(-1,3)
        keep=[]
        for p in a:
            if keep and any(np.all(q<=p) for q in keep):continue
            keep=[q for q in keep if not np.all(p<=q)];keep.append(p)
        assert {tuple(p) for p in keep}=={tuple(p) for p in saved['front']}
        if fe==100:initial_hv=volume((np.asarray(saved['front'])-norm['lower'])/norm['scale'])
    assert initial_hv is not None
    post_gain=previous_hv-initial_hv
    changed_fe=sum(v['successfulFE'] for k,v in counters.items() if k.endswith('/FA_CHANGED'))
    changed_gain=sum(v for k,v in credit.items() if k.endswith('/FA_CHANGED'))
    result={'stem':stem,'method':method,'successfulFE':500000,'actualFAChangedFE':changed_fe,
        'FAChangedPctOfPostInitialFE':100*changed_fe/499900,'FAChangedSequentialHVIncrement':changed_gain,
        'initialHV':initial_hv,'finalHV':previous_hv,'postInitialHVIncrement':post_gain,
        'FAChangedShareOfPostInitialHVIncrementPct':100*changed_gain/post_gain if post_gain>0 else None,
        'interAcceptedFAChanges':sum(r['changedJobs']>0 for r in accepted),'counters':counters,'sequentialHVCredits':credit,
        'independentRealFrontHVChecks':independent_checks,'uniquePaidAssignments':audit['uniquePaidAssignments'],
        'scope':'Sequential successful-admission attribution, conditional on actual history. FA_CHANGED may also alter JS/resources; no isolated causal payoff, same-time comparison or budget intervention.'}
    write_once(out/'fa-credit-trace.json',trace);write_once(out/'fa-analysis.json',result);return result


def analyze(root,specs):
    write_once(root/'offline-hv-checks.json',checks(hypervolume));cases=[]
    for spec in specs:
        for method in ('FULL','NSGA'):
            cases.append(analyze_case(root/spec['stem']/(method+'-ON'),spec['stem'],method,spec['normalization']))
    paired=[]
    for method in ('FULL','NSGA'):
        a=next(r for r in cases if r['stem']=='20_8_5_1' and r['method']==method)
        b=next(r for r in cases if r['stem']=='100_2_3_1' and r['method']==method)
        gap=a['FAChangedShareOfPostInitialHVIncrementPct']-b['FAChangedShareOfPostInitialHVIncrementPct']
        paired.append({'method':method,'twentyFAChangedFEAtMost5Pct':a['FAChangedPctOfPostInitialFE']<=5,
            'twentyFAHVShareAtLeast30Pct':a['FAChangedShareOfPostInitialHVIncrementPct']>=30,
            'twentyMinusHundredFAHVSharePctPoints':gap,'structureContrastAtLeast10Points':gap>=10,
            'patternSupported':bool(a['FAChangedPctOfPostInitialFE']<=5 and a['FAChangedShareOfPostInitialHVIncrementPct']>=30 and gap>=10)})
    result={'cases':cases,'predeclaredDescriptiveContrasts':paired,'supportsAllocationContinuationQuestion':all(p['patternSupported'] for p in paired),
        'limits':'One repeated development seed on two existing structurally confounded instances. No independent confirmation; even a positive pattern only motivates a separately preregistered fixed-parent continuation test.'}
    write_once(root/'analysis.json',result);return result

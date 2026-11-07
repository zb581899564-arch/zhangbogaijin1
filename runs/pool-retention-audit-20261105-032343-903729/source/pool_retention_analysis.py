"""Compare finite and complete paid objective envelopes under the identical nine policies."""
import numpy as np

from run_long_budget_bridge import read,rows,write_once
from pool_phase_analysis import candidate_cases,check_assemblies,score_cases


def full_envelope_data(data):
    snapshots=[]
    for phase in data['snapshots']:
        families=[{**family,'factories':family['fullFactories']} for family in phase['pool']['families']]
        snapshots.append({**phase,'pool':{**phase['pool'],'families':families}})
    return {**data,'snapshots':snapshots}


def analyze(root,cp,seed):
    summaries=[];qa=0
    for spec in read(root/'protocol.json')['instances']:
        stem=spec['stem'];data=rows(root/stem/str(seed)/'ON/pool-phases.jsonl')[0]
        finite_cases,finite_candidates=candidate_cases(data)
        full_data=full_envelope_data(data);full_cases,full_candidates=candidate_cases(full_data)
        unique={}
        for candidate in finite_candidates+full_candidates:
            key=tuple(tuple(candidate[k]) for k in ('JS','FA','MA','WA'))
            if key in unique:assert np.allclose(unique[key]['objectives'],candidate['objectives'],rtol=1e-12,atol=1e-9)
            else:unique[key]=candidate
        report=check_assemblies(root,cp,stem,list(unique.values()));qa+=report['passedOfflineDecodes']
        finite=score_cases(spec,data,finite_cases);full=score_cases(spec,full_data,full_cases)
        key=lambda case:(case['cohort'],case['phase'],case['receiver'])
        finite_by={key(c):c for c in finite['cases']};comparisons=[]
        for case in full['cases']:
            control=finite_by[key(case)]
            f,u=case['bestCommonGainPct'],control['bestCommonGainPct']
            comparisons.append({'cohort':case['cohort'],'phase':case['phase'],'receiver':case['receiver'],'family':case['family'],
                'fullBestCommonGainPct':f,'finiteBestCommonGainPct':u,
                'fullBestOwnGainPct':case['bestOwnPhaseGainPct'],'finiteBestOwnGainPct':control['bestOwnPhaseGainPct'],
                'materialLostSupply':f>=.1 and u<f/2})
        target=[c for c in comparisons if c['cohort']=='later' and c['phase']=='G2_CENTER_ENTRY']
        assert len(target)==8
        material=[c for c in target if c['materialLostSupply']];families=sorted({c['family'] for c in material})
        supported=len(material)/len(target)>=.2 and len(families)>=2
        detail={'stem':stem,'finite':finite,'full':full,'comparisons':comparisons,'laterEntryMaterialCases':len(material),
            'laterEntryReceivers':len(target),'materialFamilies':families,'supported':supported,
            'rawCollection':rows(root/stem/str(seed)/'ON/pool-retention.jsonl')[0]}
        write_once(root/stem/'pool-retention-opportunities.json',detail)
        summaries.append({k:v for k,v in detail.items() if k not in ('finite','full','comparisons')})
    result={'instances':summaries,'worthNewPoolRetentionProtocol':all(s['supported'] for s in summaries),
        'offlineAssemblyFullDecodes':qa,'searchFE':0,
        'scope':'Complete paid Pareto objective envelopes only, equal objective vectors represented once. Best of nine is an offline availability bound, not free online selection or search performance. No assumption of unseen future supply.'}
    write_once(root/'analysis.json',result);return result

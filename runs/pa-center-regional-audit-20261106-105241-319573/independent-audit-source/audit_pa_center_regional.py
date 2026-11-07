"""Independent full paid-state replay, assignment LP and vectorized decision tables."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from collections import Counter
from pathlib import Path
import json
import shutil
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import eye,kron,vstack

from run_long_budget_bridge import ROOT,read,rows,write_once
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from pa_role_replay import RoleReplay


def mapping_check(initial,scale,recorded):
    weights=np.array([(i,j,k) for i in range(1,11) for j in range(1,11) for k in range(1,11) if i+j+k==12],float)
    assert weights.shape==(55,3) and weights.tolist()==recorded['directions']
    points=np.array([p['objectives'] for p in initial]);ideal=points.min(axis=0)
    cost=(weights[None,:,:]*((points[15:70,None,:]-ideal)/scale)).max(axis=2)
    constraints=vstack((kron(eye(55),np.ones((1,55))),kron(np.ones((1,55)),eye(55))),format='csr')
    solution=linprog(cost.ravel(),A_eq=constraints,b_eq=np.ones(110),bounds=(0,None),method='highs')
    assert solution.success
    matched=np.array([recorded['slotDirections']['MATCHED'][str(i)] for i in range(15,70)])
    indices=[]
    for w in matched:
        found=np.flatnonzero(np.all(weights==w,axis=1));assert len(found)==1;indices.append(int(found[0]))
    assert len(set(indices))==55
    cost_sum=float(cost[np.arange(55),indices].sum())
    assert abs(cost_sum-solution.fun)<2e-9 and abs(cost_sum-recorded['matchedInitialAssignmentCost'])<2e-12
    assert [recorded['slotDirections']['LEX'][str(i)] for i in range(15,70)]==weights.tolist()
    return dict(primalLPVariables=3025,equalityConstraints=110,minimumAssignmentCost=cost_sum,LPObjectiveError=abs(cost_sum-solution.fun))


def tables(data,recorded,scale,thresholds):
    child=np.array([r['objectives'] for r in data]);parent=np.array([r['parentObjectives'] for r in data]);ideal=np.array([r['ideal'] for r in data])
    accepted=np.array([r['accepted'] for r in data],bool);checks=[]
    for mode in ('MATCHED','LEX'):
        weights=np.array([recorded['slotDirections'][mode][str(r['slot'])] for r in data])
        old=(weights*((parent-ideal)/scale)).max(axis=1);new=(weights*((child-ideal)/scale)).max(axis=1)
        observed=recorded['modes'][mode];counts=Counter(acceptedChanged=int(accepted.sum()),rejectedChanged=int((~accepted).sum()))
        for prefix,mask in (('accepted',accepted),('rejected',~accepted)):
            for suffix,relation in (('RegionalBetter',new<old),('RegionalWorse',new>old),('RegionalEqual',new==old)):
                counts[prefix+suffix]=int(np.sum(mask&relation))
        missed=(~accepted)&(new<old)
        assert all(data[i]['archiveDominated'] for i in np.flatnonzero(missed))
        counts['rejectedBetterAlreadyArchiveDominated']=int(missed.sum())
        assert {k:v for k,v in counts.items() if v}=={k:v for k,v in observed['counts'].items() if v}
        programs=sorted({(data[i]['generation'],data[i]['slot']) for i in np.flatnonzero(missed)})
        generations=sorted({p[0] for p in programs})
        assert [list(p) for p in programs]==observed['opportunityPrograms'] and generations==observed['opportunityGenerations']
        bad=counts['acceptedRegionalWorse']/counts['acceptedChanged'];opportunity=counts['rejectedRegionalBetter']/counts['rejectedChanged']
        assert bad==observed['acceptedWorseFraction'] and opportunity==observed['rejectedBetterFraction']
        gate=dict(acceptedWorse=bad>=thresholds['acceptedWorseFraction'],rejectedBetter=opportunity>=thresholds['rejectedBetterFraction'],
            differentPrograms=len(programs)>=thresholds['differentOpportunityPrograms'],bothGenerations=generations==[1,2])
        assert gate==observed['checks'] and observed['pass_']==all(gate.values())
        by_fe={r['paidFE']:i for i,r in enumerate(data)}
        for category,examples in observed['examples'].items():
            expected=[]
            for i,r in enumerate(data):
                name=('accepted' if accepted[i] else 'rejected')+('RegionalBetter' if new[i]<old[i] else 'RegionalWorse' if new[i]>old[i] else 'RegionalEqual')
                if name==category:expected.append(i)
            assert [e['fe'] for e in examples]==[data[i]['paidFE'] for i in expected[:10]]
            for e in examples:
                i=by_fe[e['fe']];assert abs(e['parentScore']-old[i])<1e-13 and abs(e['childScore']-new[i])<1e-13
        checks.append(dict(mode=mode,changedCenterDecisions=len(data),allCountsExamplesAndProgramGateVerified=True))
    return checks


def audit_case(spec,recorded,plan):
    folder=Path(spec['source']);initial=[];data=[];ideal=np.full(3,np.inf)
    for name,sha in spec['sourceHashes'].items():assert digest(folder/name)==sha
    catalog,=rows(folder/'catalog.jsonl');tasks={e['generation']:e for e in rows(folder/'role-events.jsonl')}
    replay=RoleReplay(catalog['tuples'],tasks,'NATIVE',15530003)
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line)
            if event['kind'] in ('initial','step'):ideal=np.minimum(ideal,event['objectives'])
            if event['kind']=='initial':initial.append(dict(event))
            if event['kind']=='step' and event['role']=='CENTER' and event['objectives']!=event['parentObjectives']:
                data.append(dict(event,ideal=ideal.tolist()))
            replay.event(event)
    receipt,=rows(folder/'receipt.jsonl')
    assert replay.paid==recorded['paidRowsRead']==receipt['successfulFE'] and replay.digest.hexdigest()==receipt['paidSHA256']
    assert replay.generations==2 and replay.programs==200 and receipt['fees']==dict(replay.fees)
    assert len(data)==recorded['centerChangedDecisions']
    assignment=mapping_check(initial,np.asarray(spec['scale']),recorded)
    tests=tables(data,recorded,np.asarray(spec['scale']),plan['thresholds'])
    assert recorded['pass_']==all(m['pass_'] for m in recorded['modes'].values())
    return dict(instance=spec['instance'],paidGenomeDigestArchiveAndAcceptReplayPassed=True,assignment=assignment,tables=tests)


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert read(root/'status.json')['status']=='COMPLETE' and protected()==protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/PA_CENTER_REGIONAL_AUDIT_V1.json')==protocol['contractSHA256']
    assert digest(Path(plan['sourceEngineering'])/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    checked=[audit_case(spec,case,plan) for spec,case in zip(plan['cases'],result['cases'])]
    assert result['paidRowsRead']==47800 and result['pass_']==all(c['pass_'] for c in result['cases'])
    assert result['newSearchFE']==result['newObjectiveQueries']==result['newDecoderCalls']==0
    write_once(root/'independent-final-audit.json',dict(passed=True,cases=checked,sourcePaidRowsReplayed=47800,
        newSearchFE=0,newObjectiveQueries=0,newDecoderCalls=0,performanceProved=False,goalAchieved=False))
    folder=root/'independent-audit-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('CENTER_REGIONAL_INDEPENDENT_AUDIT_PASS',47800,'existing paid rows;0newFE/queries/decoder',flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

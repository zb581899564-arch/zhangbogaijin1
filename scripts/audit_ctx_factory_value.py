"""Read-only independent pool, objective, oracle, metric and exact-witness acceptance."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
from itertools import product
import sys
import numpy as np

from run_long_budget_bridge import read,rows,write_once,nondominated
from research.semantic_repair.evidence import digest
from research.expansion_audit.metrics import grid_hv
from ctx_factory_value_pool_check import check_pools
from ctx_role_factory_contract import factory_parts
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture


def objective(parts,records):
    # Independent scalar traversal; deliberately not the assembly implementation.
    energy=0.;cost=0.;end=0.
    for f,rid in enumerate(parts):
        record=records[rid];assert record['factory']==f;end=max(end,record['objectives'][0])
        for index in range(len(record['energy'])):energy=energy+record['energy'][index]
        for index in range(len(record['labor'])):cost=cost+record['labor'][index]
    return [end,energy,cost]


def independent_metrics(case,background,norm,reference):
    expected=nondominated([*background,case['winnerObjectives']]);actual=np.array(case['metrics']['front'])
    assert np.array_equal(expected,actual)
    normal=(actual-norm['lower'])/norm['scale'];maximum=0.
    for r in (1.25,1.5,2.):
        error=abs(grid_hv(normal,r)-case['metrics']['HV'][str(r)]);assert error<2e-11;maximum=max(maximum,error)
    igd=float(np.mean([np.sqrt(np.sum(np.maximum(normal-point,0.)**2,axis=1)).min() for point in reference]))
    assert abs(igd-case['metrics']['IGDplus'])<2e-12
    return maximum


def analyze_supply(cases,queries,records):
    result=[]
    for source in ('S','U'):
        for cycle in (1,10):
            whole={r['request']:r for r in cases if r['source']==source and r['cycle']==cycle and r['schema']=='WHOLE_FA'}
            broad={r['request']:r for r in cases if r['source']==source and r['cycle']==cycle and r['schema']=='JOBSET'}
            additional=0;different=0
            for qid in whole:
                for f in range(3):
                    def chains(schema):
                        return {tuple(tuple(records[r][k]) for k in ('jobs','machines','workers')) for r in queries[qid,source,schema]['pool'][f]}
                    a,b=chains('WHOLE_FA'),chains('JOBSET');additional+=len(b-a);different+=int(a!=b)
            group=list(whole.values())+list(broad.values())
            result.append(dict(source=source,cycle=cycle,requests=len(whole),additionalCapEligibleJobsetChains=additional,
                differentFactoryChoiceSets=different,positiveOracleCases=sum(r['singleCandidateHVgain']>1e-12 for r in group),
                maxSingleCandidateGainPctOfBackground=max(r['singleCandidateGainPctOfBackground'] for r in group)))
    return result


def audit(root):
    protocol=read(root/'protocol.json');evidence=Path(protocol['evidenceRoot']);result=read(root/'analysis.json')
    original=read(evidence/'protocol.json');assert protected()==protocol['protectedBefore']==original['protectedBefore']
    for name,sha in protocol['acceptedEvidence'].items():assert digest(evidence/name)==sha
    for folder in (evidence,root):
        for name,sha in read(folder/'source-hashes.json').items():assert digest(folder/'source'/name)==sha
        assert class_hashes(folder/'classes')==read(folder/'class-hashes.json')
    for name,sha in read(evidence/'input-hashes.json').items():assert digest(evidence/'inputs'/name)==sha
    physics=read(evidence/'physics-acceptance.json');verify_capture(physics['classIdentity'],(evidence/'classpath.txt').read_text('utf-8'))
    verify_capture(read(root/'loaded-identity.json'),(root/'classpath.txt').read_text('utf-8'))
    points=read(evidence/'source-points.json');records={r['id']:r for r in rows(evidence/'factory-records.jsonl')}
    cases=read(evidence/'oracle-cases.json');queries={(r['request'],r['source'],r['schema']):r for r in rows(evidence/'query-pools.jsonl')}
    pool=check_pools(evidence,points,records,queries)
    enums=read(evidence/'oracle-enumeration.json');context=read(evidence/'metric-context.json');norm=context['normalization']
    reference=np.array(context['empiricalReference']);background=read(evidence/'backgrounds.json');objectives=0;source_not_covered=0
    checks=[];metrics_checked=set();max_hv_error=0.
    for case,enum in zip(cases,enums):
        key=case['request'],case['source'],case['schema'];assert key==(enum['request'],enum['source'],enum['schema'])
        parts=list(product(*queries[key]['pool']));assert [list(p) for p in parts]==enum['parts']
        values=[objective(p,records) for p in parts];assert values==enum['objectives'];objectives+=len(values)
        chosen=int(np.argmax(enum['gain']));assert chosen==enum['chosen'] and enum['parts'][chosen]==case['winnerParts']
        assert values[chosen]==case['winnerObjectives']
        b=np.array(background[str(case['cycle'])]);uncovered=[]
        for value in values:uncovered.append(not np.all(b<=value,axis=1).any())
        if case['source']=='S':source_not_covered+=sum(uncovered)
        # Every claimed zero-gain S composition must be exactly covered by the common archive.
        if case['source']=='S':assert not any(uncovered)
        parent=points[case['parent']];assignment,parent_parts=factory_parts(parent)
        for f,rid in enumerate(case['winnerParts']):assert set(records[rid]['jobs'])==set(parent_parts[f][1])
        front_key=tuple(map(tuple,case['metrics']['front']))
        if front_key not in metrics_checked:
            max_hv_error=max(max_hv_error,independent_metrics(case,background[str(case['cycle'])],norm,reference));metrics_checked.add(front_key)
        checks.append(dict(request=case['request'],source=case['source'],schema=case['schema'],compositions=len(parts),
            exactlyBackgroundCoveredCompositions=len(parts)-sum(uncovered)))
    assert objectives==result['logicalCompleteObjectiveCompositionQueries']
    for row in result['comparisons']:
        group={r['source']+':'+r['schema']:r for r in cases if r['request']==row['request']}
        for key,a,b in [('jobsetVsWholeFA','S:JOBSET','S:WHOLE_FA'),('SsourceVsUsource','S:JOBSET','U:JOBSET')]:
            av=group[a]['metrics'];bv=group[b]['metrics'];ac,b_c=np.array(av['front']),np.array(bv['front']);coverage=row[key]['coverage']
            covered_b=sum(any(np.all(x<=y) for x in ac) for y in b_c);covered_a=sum(any(np.all(y<=x) for y in b_c) for x in ac)
            assert covered_b==coverage['coveredB'] and covered_a==coverage['coveredA']
            assert coverage['C_A_B']==covered_b/len(b_c) and coverage['C_B_A']==covered_a/len(ac)
    witness=read(root/'witness-validation.json');assert witness['status']=='PASS' and witness['exactObjectiveBitsRequired']
    assert witness['maxAbsoluteObjectiveError']==[0.,0.,0.]
    assert not result['generalValuePass'] and not result['roleSupplyPass'] and result['generalValue']['jointMaterialRequests']==0
    for row in result['comparisons']:assert row['jobsetIncrementHV']==0. and row['jobsetVsWholeFA']['Cdelta']==0.
    accepted=dict(passed=True,**pool,independentlyReconstructedCompleteObjectiveQueries=objectives,
        exactBackgroundUncoveredSsourceCompositions=source_not_covered,uniqueAugmentedMetricFrontsChecked=len(metrics_checked),
        maximumIndependentHVError=max_hv_error,allBidirectionalCoveredCountsEqual=True,
        exactFullTimelineWitnessDecodes=witness['passedOfflineDecodes'],supplyBreakdown=analyze_supply(cases,queries,records),
        compositionChecks=checks,extraSearchFE=0,defaultMainlineChanged=False,goalAchieved=False)
    write_once(root/'independent-final-audit.json',accepted);print('FACTORY_VALUE_INDEPENDENT_AUDIT_PASS',pool,objectives,max_hv_error,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

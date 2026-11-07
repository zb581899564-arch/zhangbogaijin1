"""Bounded offline oracle; all complete-objective composition queries are explicitly counted."""
from itertools import product
import numpy as np

from run_long_budget_bridge import read,rows,write_once,hypervolume
from ctx_phase_analysis import metric,paired
from ctx_factory_value_data import assemble,vector_key
from research.composition_oracle.volume import UncoveredVolume,engineering_checks


def oracle(root):
    context=read(root/'metric-context.json');norm=context['normalization'];reference=np.array(context['empiricalReference'])
    background=read(root/'backgrounds.json');records={r['id']:r for r in rows(root/'factory-records.jsonl')}
    sources=read(root/'source-points.json');pools=rows(root/'query-pools.jsonl');cases=[];enumeration=[];witnesses={};witness_ids={}
    scorers={};baseline={};metric_cache={};logical=0;distinct=set()
    fixtures=engineering_checks(hypervolume)
    for cycle,front in background.items():
        normal=(np.asarray(front)-norm['lower'])/norm['scale'];baseline[cycle]=metric(front,norm,reference)
        for r in (1.25,1.5,2.):
            scorer=UncoveredVolume(normal,(r,)*3);assert abs(scorer.background_hv-baseline[cycle]['HV'][str(r)])<2e-11
            scorers[cycle,r]=scorer

    def witness(point):
        key=vector_key(point)
        if key not in witness_ids:
            wid=f'w{len(witnesses):03d}';witness_ids[key]=wid;witnesses[wid]=point
        return witness_ids[key]

    for query in pools:
        cycle=str(query['cycle']);combos=list(product(*query['pool']));assert 0<len(combos)<=512
        candidates=[assemble(parts,records) for parts in combos];logical+=len(combos)
        for point in candidates:distinct.add(vector_key(point))
        normal=(np.array([p['objectives'] for p in candidates])-norm['lower'])/norm['scale']
        gains=scorers[cycle,1.5].gains(normal);best=int(np.argmax(gains))
        # Pool lists and product order are lexicographic record IDs, so exact ties select first.
        chosen=candidates[best];obj=tuple(chosen['objectives']);mk=(cycle,obj)
        if mk not in metric_cache:metric_cache[mk]=metric([*background[cycle],chosen['objectives']],norm,reference)
        value=metric_cache[mk]
        assert abs(value['HV']['1.5']-baseline[cycle]['HV']['1.5']-float(gains[best]))<2e-11
        for r in (1.25,2.):
            assert abs(scorers[cycle,r].gains(normal[best:best+1])[0]-(value['HV'][str(r)]-baseline[cycle]['HV'][str(r)]))<2e-11
        witness_id=witness(chosen)
        parent=sources[query['parent']];identity=assemble([query['parent']+'#'+str(f) for f in range(3)],records)
        assert identity['objectives']==parent['objectives'];identity_id=witness(identity)
        cases.append({**query,'completeCompositionQueries':len(combos),'winnerParts':combos[best],'winnerObjectives':chosen['objectives'],
            'winnerWitness':witness_id,'identityWitness':identity_id,'singleCandidateHVgain':float(gains[best]),
            'singleCandidateGainPctOfBackground':100*float(gains[best])/baseline[cycle]['HV']['1.5'],'metrics':value})
        enumeration.append(dict(request=query['request'],source=query['source'],schema=query['schema'],parts=combos,
                                objectives=[p['objectives'] for p in candidates],gain=gains.tolist(),chosen=best))
    assert logical<=81920 and len(witnesses)<=200
    write_once(root/'oracle-enumeration.json',enumeration);write_once(root/'oracle-cases.json',cases)
    write_once(root/'witnesses.json',witnesses)
    from ctx_factory_value_data import write_tsv
    write_tsv(root/'witnesses.tsv',witnesses)
    write_once(root/'offline-counts.json',dict(extraSearchFE=0,logicalCompleteObjectiveCompositionQueries=logical,
        distinctComposedGenomes=len(distinct),partialFactoryRecords=len(records),singlePointHVgainQueries=logical+2*len(cases),
        sourcePoints=len(sources),distinctWitnessFullDecodeRequests=len(witnesses),HVEngineFixtures=fixtures))
    return decide(cases,baseline)


def comparisons(cases):
    groups={}
    for case in cases:groups.setdefault(case['request'],{})[case['source'],case['schema']]=case
    result=[]
    for request,group in groups.items():
        first=next(iter(group.values()));s=group['S','JOBSET'];whole=group['S','WHOLE_FA'];u=group['U','JOBSET']
        result.append(dict(request=request,cycle=first['cycle'],fe=first['fe'],parent=first['parent'],aliases=first['aliases'],
            jobsetVsWholeFA=paired(s['metrics'],whole['metrics']),SsourceVsUsource=paired(s['metrics'],u['metrics']),
            jobsetIncrementHV=s['singleCandidateHVgain']-whole['singleCandidateHVgain'],
            sourceIncrementHV=s['singleCandidateHVgain']-u['singleCandidateHVgain'],
            SsourceMissing=s['missingFactoryContexts'],UsourceMissing=u['missingFactoryContexts']))
    return result


def decide(cases,baseline):
    comparisons_=comparisons(cases);late=[r for r in comparisons_ if r['cycle']==10]
    threshold=.001*baseline['10']['HV']['1.5']

    def joint(row,key,increment,sign=1):
        value=row[key]
        return sign*row[increment]>1e-12 and sign*value['IGDplusSymmetricWorseningPct']<=1e-10 and sign*value['Cdelta']>=0

    good=[r for r in late if r['jobsetIncrementHV']>=threshold and joint(r,'jobsetVsWholeFA','jobsetIncrementHV')]
    # Count distinct actual FA contexts, not two receivers sharing one family.
    # Context identities are attached below by the controller from frozen parents.
    general=dict(lateRequests=len(late),jointMaterialRequests=len(good),fraction=len(good)/len(late) if late else 0.,
                 materialRequestIDs=[r['request'] for r in good],minimumContexts=2)
    supply={}
    for kind in ('S','U'):
        eligible=[r for r in comparisons_ if any(a[2].startswith(kind+':') and int(a[1])>=0 for a in r['aliases'])
                  and not r['SsourceMissing'] and not r['UsourceMissing']]
        wins=sum(joint(r,'SsourceVsUsource','sourceIncrementHV') for r in eligible)
        losses=sum(joint(r,'SsourceVsUsource','sourceIncrementHV',-1) for r in eligible)
        material=[r for r in eligible if r['sourceIncrementHV']>=.001*baseline[str(r['cycle'])]['HV']['1.5']
                  and joint(r,'SsourceVsUsource','sourceIncrementHV')]
        families={int(a[1]) for r in eligible for a in r['aliases'] if a[2].startswith(kind+':') and int(a[1])>=0}
        supply[kind]=dict(requests=len(eligible),families=sorted(families),jointWins=wins,jointLosses=losses,
            jointMaterialRequests=len(material),materialFraction=len(material)/len(eligible) if eligible else 0.,
            pass_=wins>losses and bool(eligible) and len(material)/len(eligible)>=.2)
    fixed_ids={r['request'] for r in comparisons_ if any(int(a[1])>=0 for a in r['aliases']) and not r['SsourceMissing'] and not r['UsourceMissing']}
    fixed_families={int(a[1]) for r in comparisons_ if r['request'] in fixed_ids for a in r['aliases'] if int(a[1])>=0}
    return dict(comparisons=comparisons_,generalValue=general,roleSupply=supply,
        compatibleFixedFamilyRequests=len(fixed_ids),compatibleFixedFamilies=sorted(fixed_families),
        roleSupplyPass=len(fixed_ids)>=8 and len(fixed_families)>=2 and all(s['pass_'] for s in supply.values()),
        arithmeticTolerance='1e-12 absolute HV to suppress summation-only signs; 1e-10 pct IGD+; exact C counts',
        archiveAdditionWarning='Adding one point weakly improves an archive by construction; compare oracle augmented fronts, not monotonicity against background',
        extraSearchFE=0,defaultMainlineChanged=False,sameTimeTested=False,goalAchieved=False)

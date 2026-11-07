"""Structural-only model/proposal sensitivity; never turns a hash change into a quality gain."""
from collections import Counter,defaultdict
import csv
import numpy as np

from run_long_budget_bridge import read,rows,write_once


def nonsingleton(subsets):
    return {tuple(mask) for mask in subsets if len(mask)>1}


def summarize(root,populations,plan):
    models={};native_checks=0
    for stem in ('20_8_5_1','100_2_3_1'):
        for model in rows(root/stem/'models.jsonl'):models[model['population'],model['variant']]=model
    results={};original_proposals={};counts=defaultdict(lambda:defaultdict(Counter));witnesses=[];total=0
    for population in populations:
        pid=population['id'];original=models[pid,'ORIGINAL'];original_fos=nonsingleton(original['qpaActiveSubsets']);views=[]
        if 'originalAffinity' in population:
            assert np.array_equal(np.array(population['originalAffinity']),np.array(original['qpaAffinity']))
            assert population['originalActiveSubsets']==original['qpaActiveSubsets'];native_checks+=1
        for variant in plan['variants']:
            model=models[pid,variant];fos=nonsingleton(model['qpaActiveSubsets'])
            assert model['paGenes']==original['paGenes'] and model['paAffinity']==original['paAffinity'] and model['paSubsets']==original['paSubsets']
            views.append(dict(variant=variant,maxQpaAffinityChange=float(np.max(np.abs(np.array(model['qpaAffinity'])-original['qpaAffinity']))),
                nonSingletonFOSJaccard=len(fos&original_fos)/len(fos|original_fos) if fos|original_fos else 1.,
                qpaActiveMasks=len(model['qpaActiveSubsets']),paGenesModelAndFOSEqual=True))
        results[pid]=dict(population=pid,instance=population['instance'],evolved=population['evolved'],views=views)
    for stem in ('20_8_5_1','100_2_3_1'):
        with (root/stem/'proposal-hashes.tsv').open(encoding='utf-8') as stream:
            for row in csv.DictReader(stream,delimiter='\t'):
                total+=1;pid,variant=row['population'],row['variant'];key=(pid,int(row['pair']),int(row['mask']),row['kind'])
                if variant=='ORIGINAL':original_proposals[key]=row;continue
                old=original_proposals[key];assert row['reference']==old['reference'] and row['fallback']==old['fallback']
                group=counts[pid][variant];kind='pa' if row['kind']=='PA' else 'qpa'
                changed=row['physicalSHA256']!=old['physicalSHA256'];group[kind+'Proposals']+=1;group[kind+'PhysicalChanged']+=changed
                group[kind+'Fallback']+=row['fallback']=='true'
                if kind=='pa':assert not changed
                elif changed and len(witnesses)<8:witnesses.append(dict(population=pid,variant=variant,pair=int(row['pair']),mask=int(row['mask']),
                    kind=row['kind'],reference=int(row['reference']),originalPhysicalSHA256=old['physicalSHA256'],changedPhysicalSHA256=row['physicalSHA256']))
    for pid,item in results.items():
        overall=Counter()
        for view in item['views']:
            if view['variant']=='ORIGINAL':continue
            group=counts[pid][view['variant']];view.update(group);view['physicalProposalChangedFraction']=group['qpaPhysicalChanged']/group['qpaProposals'];overall.update(group)
        alternative=[v for v in item['views'] if v['variant']!='ORIGINAL']
        fraction=overall['qpaPhysicalChanged']/overall['qpaProposals'];low=sum(v['nonSingletonFOSJaccard']<=.8 for v in alternative)
        item.update(total=dict(overall),aggregatePhysicalProposalChangedFraction=fraction,lowFOSJaccardViews=low,coveragePass=low>=8 and fraction>=.2)
    evolved=[r for r in results.values() if r['evolved']];assert len(evolved)==2
    passed=all(r['coveragePass'] for r in evolved)
    receipts=[read(root/stem/'receipt.json') for stem in ('20_8_5_1','100_2_3_1')]
    assert total==sum(r['unscoredCompleteProposalConstructions'] for r in receipts)<=plan['maximumUnscoredCompleteProposalConstructions']
    assert sum(r['modelBuilds'] for r in receipts)==len(models)*2==plan['maximumModelBuilds']
    result=dict(populations=list(results.values()),necessaryCoveragePass=passed,originalNativeModelsRechecked=native_checks,
        knownPhysicalCarriers=sum(r['knownPhysicalCarrierInitializations'] for r in receipts),modelBuilds=len(models)*2,
        unscoredCompleteProposalConstructions=total,physicalChangeWitnesses=witnesses,
        decision='STRUCTURAL_SENSITIVITY_ONLY_SEPARATE_CAUSAL_CONTRACT_REQUIRED' if passed else 'STOP_FIXED_NEUTRAL_COORDINATE_GAP_EXPLANATION',
        newSearchFE=0,newDecoderCalls=0,completeObjectiveQueries=0,defaultMainlineChanged=False,performanceProved=False,goalAchieved=False)
    write_once(root/'analysis.json',result);return result

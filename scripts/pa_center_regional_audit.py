"""Read-only classification of existing CENTER decisions under fixed regional objectives."""
from collections import Counter,defaultdict
import json
import numpy as np
from scipy.optimize import linear_sum_assignment

from run_long_budget_bridge import rows,read


def directions():
    #55 positive integer directions; their common denominator12 does not affect comparisons.
    result=[(a+1,b+1,10-a-b) for a in range(10) for b in range(10-a)]
    assert len(set(result))==55 and all(min(w)>0 and sum(w)==12 for w in result)
    return result


def score(point,ideal,scale,weight):
    return max(w*((x-z)/s) for x,z,s,w in zip(point,ideal,scale,weight))


def assignments(initial,scale):
    centers=[(i,p) for i,p in enumerate(initial) if p['role']=='CENTER']
    assert [i for i,_ in centers]==list(range(15,70))
    weights=directions();ideal=np.min([p['objectives'] for p in initial],axis=0)
    cost=np.asarray([[score(p['objectives'],ideal,scale,w) for w in weights] for _,p in centers])
    r,c=linear_sum_assignment(cost);assert np.array_equal(r,np.arange(55))
    return dict(MATCHED={slot:weights[int(c[k])] for k,(slot,_) in enumerate(centers)},
        LEX={slot:weights[k] for k,(slot,_) in enumerate(centers)}),float(cost[r,c].sum())


def advance(event,population):
    kind=event['kind']
    if kind=='initial':
        assert event['slot']==len(population);population.append(event)
    elif kind=='reencode':
        old=population[event['slot']]
        assert event['beforeId']==old['id'] and event['paidFE']==old['paidFE'] and event['objectives']==old['objectives']
        population[event['slot']]=event
    elif kind=='step':
        assert event['parentId']==population[event['slot']]['id'] and event['parentObjectives']==population[event['slot']]['objectives']
        assert event['donorId']==population[event['donorSlot']]['id']
        own={'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}.get(event['role']);a,b=event['objectives'],event['parentObjectives']
        keep=(all(x<=y for x,y in zip(a,b)) or not event['archiveDominated']) if own is None else a[own]<b[own]
        assert keep==event['accepted']
        if keep:population[event['slot']]=event
    elif kind=='programEnd':assert event['result']['id']==population[event['slot']]['id']
    elif kind=='generationEnd':assert [p['id'] for p in event['population']]==[p['id'] for p in population]
    else:assert kind=='model'


def summarize(counts,programs,generations,examples,thresholds):
    accepted=counts['acceptedChanged'];rejected=counts['rejectedChanged']
    bad=counts['acceptedRegionalWorse']/accepted if accepted else None
    missed=counts['rejectedRegionalBetter']/rejected if rejected else None
    checks=dict(acceptedWorse=bad is not None and bad>=thresholds['acceptedWorseFraction'],
        rejectedBetter=missed is not None and missed>=thresholds['rejectedBetterFraction'],
        differentPrograms=len(programs)>=thresholds['differentOpportunityPrograms'],
        bothGenerations=sorted(generations)==[1,2])
    return dict(counts=dict(counts),acceptedWorseFraction=bad,rejectedBetterFraction=missed,
        opportunityPrograms=[list(p) for p in sorted(programs)],opportunityGenerations=sorted(generations),
        examples=examples,checks=checks,pass_=all(checks.values()))


def analyze(folder,scale,thresholds):
    population=[];initial=[];ideal=np.full(3,np.inf);paid=steps=programs=generations=0
    counts={m:Counter() for m in ('MATCHED','LEX')};opportunities={m:set() for m in counts};opportunity_generations={m:set() for m in counts}
    examples={m:defaultdict(list) for m in counts};weights=None;matched_cost=None
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line);kind=event['kind']
            if kind in ('initial','step'):
                paid+=1;assert event['paidFE']==paid;ideal=np.minimum(ideal,event['objectives'])
            if kind=='initial':
                initial.append(event)
                if len(initial)==100:weights,matched_cost=assignments(initial,scale)
            if kind=='step':
                steps+=1;a,b=event['objectives'],event['parentObjectives']
                if event['role']=='CENTER' and a!=b:
                    for mode,mapping in weights.items():
                        c=counts[mode];keep=event['accepted'];c['acceptedChanged' if keep else 'rejectedChanged']+=1
                        w=mapping[event['slot']];parent=score(b,ideal,scale,w);child=score(a,ideal,scale,w)
                        category=('accepted' if keep else 'rejected')+('RegionalBetter' if child<parent else 'RegionalWorse' if child>parent else 'RegionalEqual')
                        c[category]+=1
                        if keep and child>parent:
                            assert not event['archiveDominated'] and not all(x<=y for x,y in zip(a,b))
                        if not keep and child<parent:
                            assert event['archiveDominated'];c['rejectedBetterAlreadyArchiveDominated']+=1
                            opportunities[mode].add((event['generation'],event['slot']));opportunity_generations[mode].add(event['generation'])
                        if len(examples[mode][category])<10:
                            examples[mode][category].append(dict(fe=paid,generation=event['generation'],slot=event['slot'],parent=b,child=a,
                                weight=list(w),ideal=ideal.tolist(),parentScore=parent,childScore=child,archiveDominated=event['archiveDominated']))
            if kind=='programEnd':programs+=1
            if kind=='generationEnd':generations+=1
            advance(event,population)
    receipt,=rows(folder/'receipt.jsonl');assert paid==receipt['successfulFE']==receipt['attemptedFE'] and receipt['failedFE']==0
    assert steps==paid-100 and programs==receipt['completedPrograms']==200 and generations==receipt['completedGenerations']==2
    for row,current in zip(receipt['lastPopulation'],population):assert row['id']==current['id'] and row['objectives']==current['objectives']
    modes={m:summarize(counts[m],opportunities[m],opportunity_generations[m],dict(examples[m]),thresholds) for m in counts}
    return dict(paidRowsRead=paid,centerChangedDecisions=sum(counts['MATCHED'][k] for k in ('acceptedChanged','rejectedChanged')),
        directions=[list(w) for w in directions()],slotDirections={m:{str(i):list(w) for i,w in mapping.items()} for m,mapping in weights.items()},
        matchedInitialAssignmentCost=matched_cost,modes=modes,pass_=all(m['pass_'] for m in modes.values()))

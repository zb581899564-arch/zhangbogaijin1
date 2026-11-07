"""Joint quality and support summaries; no winner-weighted aggregate score."""
from collections import Counter
import numpy as np
import moocore
from common import *


def hv(points, ref=1.5):
    return float(moocore.hypervolume(np.asarray(points)/SCALE, ref=[ref]*3))


def symmetric_improvement(a, b):
    return 200*(b-a)/(a+b) if a+b else 0.


def comparison(a, b, reference):
    ma, mb = metrics(a, reference, SCALE), metrics(b, reference, SCALE)
    ab, ba = coverage(a, b), coverage(b, a)
    changes = {str(r): 100*(hv(a, r)/hv(b, r)-1) for r in (1.25, 1.5, 2.0)}
    return dict(HVpercent=changes['1.5'], HVsensitivity=changes,
                IGDplusImprovementPercent=symmetric_improvement(ma['IGDplus'], mb['IGDplus']),
                IGDImprovementPercent=symmetric_improvement(ma['IGD'], mb['IGD']),
                C_A_B=ab, C_B_A=ba, coverageDifferencePP=100*(ab['C']-ba['C']))


def outcomes(entry, arm, queries, actual, reference, background='A0'):
    selected = [q for q in queries.values() if q['context'] == entry['id'] and q['arm'] == arm]
    before = np.asarray(entry[background]);base_hv = hv(before)
    new = [actual[q['id']]['objectives'] for q in selected]
    front = nd([*before, *new]);base = metrics(before, reference, SCALE)
    summary = dict(context=entry['id'], arm=arm, background=background, FE=len(selected),
                   base=base, final=metrics(front, reference, SCALE),
                   deltaHV=hv(front)-base_hv, relativeGainHVpercent=100*(hv(front)/base_hv-1),
                   extrema=[front[np.argmin(front[:,k])].tolist() for k in range(3)])
    singles = []
    for q, objectives in zip(selected, new):
        fresh = not bool(np.any(np.all(before <= objectives, axis=1)))
        single = hv([*before, objectives])-base_hv if fresh else 0.
        singles.append(dict(id=q['id'], context=entry['id'], arm=arm, role=q['role'],
                            fresh=fresh, singleDeltaHV=single, fallback=q['fallback']))
    summary.update(freshCandidates=sum(s['fresh'] for s in singles), uniqueFreshObjectives=len({tuple(v) for v,s in zip(new,singles) if s['fresh']}),
                   maxSingleDeltaHV=max(s['singleDeltaHV'] for s in singles),
                   meanSingleDeltaHV=float(np.mean([s['singleDeltaHV'] for s in singles])),
                   fallbacks=sum(q['fallback'] for q in selected))
    return front, summary, singles


def trigger_and_structure(entry, queries, actual, catalog):
    parents = {p['slot']:p for p in entry['S']}
    s_free = [p for p in entry['S'] if p['family'] == -1]
    support = [{p['resources'][j] for p in s_free} for j in range(100)]
    result = {}
    base = np.asarray(entry['A0'])
    for arm in ARMS:
        selected = [q for q in queries.values() if q['context'] == entry['id'] and q['arm'] == arm]
        changed, absent, fa_changed, new_capacity = [], [], [], []
        for q in selected:
            original = queries[q['proposal']+'-S_RESOURCE'];p=parents[q['receiver']]
            changed.append(physical(q) != physical(original))
            absent.append(sum(r not in support[j] for j,r in enumerate(q['resources'])))
            fa_changed.append(any(catalog[r][0] != catalog[p['resources'][j]][0] for j,r in enumerate(q['resources'])))
            new_capacity.append(not bool(np.any(np.all(base <= actual[q['id']]['objectives'], axis=1))))
        result[arm] = dict(changedFromS=sum(changed), withAbsentShareTuples=sum(v>0 for v in absent),
            totalAbsentTupleOccurrences=sum(absent), withFAChange=sum(fa_changed),
            freshWithAbsentTuples=sum(n and a>0 for n,a in zip(new_capacity,absent)),
            freshWithoutAbsentTuples=sum(n and a==0 for n,a in zip(new_capacity,absent)))
    return dict(context=entry['id'], arms=result)


def decide(comparisons, triggers):
    primary = [r for r in comparisons if r['background']=='A0' and r['comparison']=='PA_RESOURCE_vs_S_RESOURCE']
    coherent = [r for r in comparisons if r['background']=='A0' and r['comparison']=='PA_RESOURCE_vs_PA_SHUFFLED']
    def adverse(r):
        return r['HVpercent'] < -0.1 or r['IGDplusImprovementPercent'] < -5 or r['coverageDifferencePP'] < -10
    signal = [r['context'] for r in primary if (r['HVpercent'] >= .1 or r['IGDplusImprovementPercent'] >= 5) and not adverse(r)]
    trigger = all(t['arms']['PA_RESOURCE']['changedFromS'] >= 20 for t in triggers)
    passed = trigger and len(signal)>=2 and not any(adverse(r) for r in primary)
    correlation = [r['context'] for r in coherent if (r['HVpercent'] >= .05 or r['IGDplusImprovementPercent'] >= 2.5)
                   and r['HVpercent'] >= 0 and r['IGDplusImprovementPercent'] >= 0 and r['coverageDifferencePP'] >= 0]
    return dict(resourceSourceWorthFurtherStudy=passed, meaningfulContexts=signal, triggerAdequate=trigger,
                majorReverseContexts=[r['context'] for r in primary if adverse(r)],
                crossJobCorrelationSignal=len(correlation)>=2 and not any(adverse(r) for r in coherent),
                coherentContexts=correlation, decision='CONDITIONAL_CAPACITY_SIGNAL' if passed else 'STOP_RESOURCE_SOURCE_HYPOTHESIS_AT_THIS_SCOPE',
                fullAlgorithmPromotion=False, mainlineChanged=False, independentSeeds=1, correlatedContexts=3)

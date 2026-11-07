"""Saved-vector domain support only; no decoder, new proposal, or objective query."""
from collections import Counter
import numpy as np

from run_long_budget_bridge import rows, nondominated, hypervolume
from qpa_capability_analysis import endpoint
from ctx_phase_analysis import metric
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage


def tuples_by_job(point):
    n = len(point['JS'])
    assert sorted(point['JS']) == list(range(n))
    result = [None]*n
    for j, f, m, w in zip(point['JS'], point['FA'], point['MA'], point['WA']):
        result[j] = f, m, w
    return result


def domains(points):
    return [set(column) for column in zip(*(tuples_by_job(p) for p in points))]


def missing(point, support):
    return [j for j, value in enumerate(tuples_by_job(point)) if value not in support[j]]


def terminal(folder):
    points = [p for p in rows(folder/'checkpoint-solutions.jsonl') if p['checkpointKind'] == 'FE' and p['checkpoint'] == 500000]
    assert len({tuple(p['objectives']) for p in points}) == len(points)
    assert sorted(tuple(p['objectives']) for p in points) == sorted(map(tuple, endpoint(folder, 'FE500K', 500000)['front']))
    assert all(p['bornFE'] <= 500000 for p in points)
    return points


def initial_check(shared, ordinary):
    names = ('JS', 'FA', 'MA', 'WA', 'objectives')
    a, b = rows(shared/'initial-population.jsonl'), rows(ordinary/'initial-population.jsonl')
    assert len(a) == len(b) == 100 and all(all(x[k] == y[k] for k in names) for x, y in zip(a, b))
    for group in range(4):
        values = [tuple(v[0] for v in tuples_by_job(p)) for p in a[5*group:5*group+5]]
        assert len(set(values)) == 1
    return a


def partition_case(stem, seed, initial, targets, shared, norm, reference):
    all_domain, free_domain = domains(initial), domains(initial[20:])
    misses = [missing(p, free_domain) for p in targets]
    assert not any(missing(p, all_domain) for p in targets), 'Ordinary PA escaped its recorded initial domain'
    free = [p['objectives'] for p, absent in zip(targets, misses) if not absent]
    shared_values = [p['objectives'] for p in shared]
    full = metric(shared_values+[p['objectives'] for p in targets], norm, reference)
    reduced = metric(shared_values+free, norm, reference)
    pa = metric([p['objectives'] for p in targets], norm, reference)
    lost = {r: 100*(full['HV'][r]-reduced['HV'][r])/pa['HV'][r] for r in full['HV']}
    fraction = sum(bool(m) for m in misses)/len(targets)
    coverage = bidirectional_coverage(full['front'], reduced['front'])
    return dict(instance=stem, seed=seed, targetRecordedSchedules=len(targets),
        targetRecordedSchedulesNeedingInitialFixedOnlyTuples=sum(bool(m) for m in misses), targetFraction=fraction,
        fullInitialDomainCoversAllRecordedTargets=True, initialFreeTupleCounts=list(map(len, free_domain)),
        initialAllTupleCounts=list(map(len, all_domain)), missingJobsByTarget=misses,
        empiricalFullUnion=full, empiricalFreeSupportedUnion=reduced, pa=pa,
        lostHVRelativeToPAHVPercent=lost, fullVsReducedCoverage=coverage,
        preconditionPass=fraction >= .2 and lost['1.5'] >= .1 and min(lost['1.25'], lost['2.0']) > 0.)


def pipeline_access(path, targets, source_initial):
    observations = []; ever = [set() for _ in range(len(targets[0]['JS']))]
    initialized = False
    for event in rows(path):
        if event['kind'] != 'population':
            continue
        points = event['points']
        if event['phase'] == 'INITIAL':
            assert len(points) == 100
            for index, (a, b) in enumerate(zip(points, source_initial)):
                assert a['family'] == (index//5 if index < 20 else -1)
                assert all(a[k] == b[k] for k in ('JS', 'FA', 'MA', 'WA', 'objectives'))
            initialized = True
        if event['phase'] != 'POST_GLOBAL':
            continue
        assert initialized and len(points) == 100
        assert Counter(p['family'] for p in points) == Counter({-1: 80, 0: 5, 1: 5, 2: 5, 3: 5})
        free = domains([p for p in points if p['family'] == -1]); all_points = domains(points)
        all_ok = [not missing(p, all_points) for p in targets]
        free_ok = [not missing(p, free) for p in targets]
        blocked = [i for i, (a, b) in enumerate(zip(all_ok, free_ok)) if a and not b]
        for job, values in enumerate(free):
            ever[job].update(values)
        observations.append(dict(cycle=event['cycle'], fe=event['fe'], targetCount=len(targets),
            all100Supported=sum(all_ok), free80Supported=sum(free_ok), blockedByDomain=len(blocked),
            blockedFraction=len(blocked)/len(targets), blockedTargetIndices=blocked))
    assert initialized and len(observations) == 20
    qualified = sum(r['blockedFraction'] >= .1 for r in observations)
    return dict(observations=observations, passes=len(observations), materiallyBlockedPasses=qualified,
        everFreeAlleleSupportedTargets=sum(not missing(p, ever) for p in targets), targetCount=len(targets),
        initialMetadataConfirmedFromActualRecords=True, preconditionPass=qualified/len(observations) >= .2)

"""Focused migration, observer, stage lifecycle and strict budget acceptance."""
from collections import Counter
from run_support import initial, front_map, rows, read, run_case, write, accounting


def lifecycle(out, arm, receipt):
    fees = receipt['trace']['phaseFE']
    assert sum(fees.get(k, 0) for k in ('INITIAL', 'GLOBAL', 'LOCAL', 'LIFECYCLE')) == receipt['successful']
    assert fees.get('LIFECYCLE', 0) == 0
    gom = receipt['search']['contextGom']
    if arm == 'GLOBAL_ONLY':
        assert fees.get('LOCAL', 0) == gom['localEvaluations'] == gom['passesStarted'] == gom['preparedViews'] == 0
    if arm == 'LOCAL_ONLY':
        assert fees.get('GLOBAL', 0) == 0
        assert not any('SHARED_COMPOSITION' in k for k in fees)
    selections = []
    for r in rows(out / 'stage-events.jsonl'):
        if r['kind'] == 'selection':
            selections.append(r)
            assert r['candidateCount'] == (100 if arm == 'GLOBAL_ONLY' else 200)
            assert len(r['selected']) == 100 and sorted(r['quotas']) == [5, 5, 5, 5, 80]
        if r['kind'] == 'population' and r['label'] in ('INITIAL', 'SURVIVORS'):
            assert len(r['points']) == 100
            counts = sorted(Counter(p['family'] for p in r['points']).values())
            assert counts == [5, 5, 5, 5, 80], counts
    return len(selections)


def engineering(payload, build, java, root, plan):
    result = {'checks': [], 'platformDifferences': [], 'sameTimeClaim': False}
    seed = plan['engineeringSeed']
    for spec in plan['instances']:
        instance = spec['stem']
        base = root / instance
        baseline = run_case(payload, build, java, base/'frozen', instance, seed, 'FULL', 60000, baseline=True)
        off = run_case(payload, build, java, base/'observer-off', instance, seed, 'FULL', 60000, observation=False)
        complete = {}
        for arm in plan['arms']:
            out = base / arm
            receipt = run_case(payload, build, java, out, instance, seed, arm, 60000)
            complete[arm] = receipt
            assert initial(out) == initial(base/'frozen')
            assert lifecycle(out, arm, receipt) > 0
        full = complete['FULL']
        assert full['paidSHA256'] == off['paidSHA256'] == baseline['paidSHA256']
        common = set(front_map(base/'FULL')) & set(front_map(base/'frozen'))
        assert all(front_map(base/'FULL')[k] == front_map(base/'frozen')[k] for k in common)
        assert front_map(base/'FULL') == front_map(base/'observer-off')
        windows = payload / 'windows-reference' / instance
        old = front_map(windows)
        comparison = {'instance': instance, 'initialExactlyEqual': initial(windows) == initial(base/'frozen'),
                      'sharedCheckpoints': {str(k): old[k] == front_map(base/'frozen')[k] for k in sorted(set(old)&set(front_map(base/'frozen')))}}
        result['platformDifferences'].append(comparison)
        for arm, limit in [('FULL', 5200), ('GLOBAL_ONLY', 200), ('LOCAL_ONLY', 500)]:
            physics = run_case(payload, build, java, base/('physics-'+arm), instance, seed, arm, limit, physics=True)
            assert physics['physicsQA']['fullTimelineChecks'] == limit
        result['checks'].append({'instance': instance, 'fullFrozenPaidSequenceEqual': True, 'observationInvariant': True,
                                 'initial100Equal': True, 'phaseLifecycleAndFees': True, 'fullIncrementalTimeline': True})
    instance = plan['instances'][0]['stem']
    for arm, limit in [('FULL', 1), ('FULL', 2), ('FULL', 100), ('FULL', 5100), ('FULL', 5101),
                       ('GLOBAL_ONLY', 5101), ('LOCAL_ONLY', 101)]:
        out = root / 'boundaries' / (arm+'-'+str(limit))
        run_case(payload, build, java, out, instance, seed, arm, limit)
        assert limit in front_map(out)
    failure = run_case(payload, build, java, root/'expected-failure', instance, seed, 'FULL', 100, failure=2)
    result.update(passed=True, fees=accounting(root), expectedFailure={'attempted': 2, 'successful': 1, 'failed': 1},
                  absentPhaseRng='Entire generating branches including reencoder bypassed; no fake slots or RNG advances',
                  physicsQA=sum(rows(p)[0].get('physicsQA', {}).get('fullTimelineChecks', 0) for p in root.rglob('run-receipt.jsonl')))
    write(root / 'acceptance.json', result)
    return result

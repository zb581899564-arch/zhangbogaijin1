"""Accounting, scalar-decision and task-ownership acceptance for the isolated pilot."""
import numpy as np

from run_long_budget_bridge import read, rows, write_once
from natural_local_support import ledger_rows
from center_task_design import LIMIT


def verify_cutoff(out, limit, ledger_path):
    receipt, = rows(out / 'run-receipt.jsonl')
    assert receipt['error'] is None and receipt['stopReason'] == 'FE_LIMIT'
    assert receipt['successful'] == receipt['attempted'] == receipt['decoder']['dynamic.evaluations'] == limit
    assert receipt['failed'] == 0
    search = receipt['search']
    assert sum(search.get(k + '.evaluations', 0) for k in ('initialization', 'global', 'inter', 'intra')) == limit
    actual, expected = ledger_rows(out / 'local-ledger.csv'), ledger_rows(ledger_path)
    assert len(actual) <= len(expected)
    for i, (got, want) in enumerate(zip(actual, expected)):
        assert all(got[k] == want[k] for k in ('visit', 'group', 'round', 'factory'))
        assert 0 <= got['paid'] <= want['paid']
        if i < len(actual) - 1: assert got['paid'] == want['paid']
    assert sum(r['paid'] for r in actual) == sum(search.get(k + '.evaluations', 0) for k in ('inter', 'intra'))
    validation = read(out / 'checkpoint-validation.json')
    assert validation['status'] == 'passed' and validation['allReachedPointsCovered'] and validation['extraSearchFE'] == 0
    write_once(out / 'accounting-acceptance.json', {'status': 'PASS', 'successfulFE': limit,
        'attemptedFE': limit, 'unexpectedEvaluationFailures': 0, 'ledgerSlots': len(actual),
        'checkpointFullDecoderQA': validation['uniqueOfflineDecodes'], 'prefixCleanupAccepted': True})
    return receipt


def verify_scalar_audit(out, scale):
    weights = [[a / 12, b / 12, (12 - a - b) / 12]
               for a in range(1, 11) for b in range(1, 12 - a)]
    records = rows(out / 'center-task-audit.jsonl'); stages = {}
    for item in records:
        stages[item['stage']] = stages.get(item['stage'], 0) + 1
        ideal = np.asarray(item['ideal']); weight = np.asarray(weights[item['weight']])
        def score(point): return float(np.max(weight * (np.asarray(point) - ideal) / scale))
        if item['stage'] == 'PERSONAL':
            selected = min(item['history'], key=score)
            assert selected == item['chosen']
        else:
            before, after = score(item['before']), score(item['after'])
            assert abs(before - item['beforeScore']) < 1e-12 and abs(after - item['afterScore']) < 1e-12
            assert (after < before) == item['accepted']
    write_once(out / 'scalar-decision-acceptance.json', {'status': 'PASS', 'records': len(records),
        'stages': stages, 'method': 'Independent Python recomputation from paid ideal, fixed scale and raw objectives'})


def verify_tasks(out, arm, limit, scale, scalar_audit):
    data, = rows(out / 'center-tasks.json'); counts = data['counts']; events = data['events']
    mode = 'OFF' if arm == 'NSGA' else arm
    assert data['mode'] == mode and data['activeLocalCleared']
    if mode == 'OFF': assert not counts and not events
    else:
        assert counts['successfulPaidIdealUpdates'] == limit
        assert counts.get('localEntries', 0) == counts.get('localExits', 0)
        for event in events:
            assert sorted(event['slots']) == list(range(55))
            assert sorted(event['categories']) == [0] * 47 + [1] * 2 + [2] * 2 + [3] * 2 + [4] * 2
            values = event['weights']
            if mode == 'FIXED': assert values == event['slots']
            elif mode == 'EQUAL': assert values == [-1] * 55
            elif mode == 'OWNER_PDDR': assert values == [-2] * 55
            else: assert sorted(values) == list(range(55))
        if limit == LIMIT:
            for key, expected in {'completeTaskRetentions': 2, 'endGlobalLocalPairs': 200,
                                  'centerGlobalPairs': 5500, 'localEntries': 200}.items():
                assert counts[key] == expected, (key, counts.get(key), expected)
            if mode != 'OWNER_PDDR':
                assert counts['taskPersonalQueries'] == 5500 and counts['taskGroupRewards'] == 100
        if limit == 13300: assert counts['completeTaskRetentions'] == 1
    if scalar_audit: verify_scalar_audit(out, np.asarray(scale))
    write_once(out / 'task-acceptance.json', {'status': 'PASS', 'mode': mode,
        'actualPaidIdealUpdates': counts.get('successfulPaidIdealUpdates', 0),
        'generationRetentions': counts.get('completeTaskRetentions', 0), 'events': len(events)})


def off_equivalence(original, shadow):
    a, = rows(original / 'run-receipt.jsonl'); b, = rows(shadow / 'run-receipt.jsonl')
    assert a['paidSHA256'] == b['paidSHA256'] and len(a['paidSHA256']) == 64
    assert a['search'] == b['search']
    assert {k: v for k, v in a['decoder'].items() if k != 'dynamic.decodeNanos'} == {
        k: v for k, v in b['decoder'].items() if k != 'dynamic.decodeNanos'}
    for name in ('initial-population.jsonl', 'local-ledger.csv'):
        assert (original / name).read_bytes() == (shadow / name).read_bytes()
    fronts = [{r['checkpoint']: r['front'] for r in rows(p / 'anytime.jsonl')
               if r['checkpointKind'] == 'FE' and r['reached']} for p in (original, shadow)]
    for fe in fronts[0].keys() & fronts[1].keys(): assert fronts[0][fe] == fronts[1][fe]
    keys = ('objectives', 'JS', 'FA', 'MA', 'WA', 'bornFE')
    genes = [{(r['checkpointKind'], r['checkpoint']): [] for r in rows(p / 'checkpoint-solutions.jsonl')}
             for p in (original, shadow)]
    for i, folder in enumerate((original, shadow)):
        for item in rows(folder / 'checkpoint-solutions.jsonl'):
            genes[i][(item['checkpointKind'], item['checkpoint'])].append({k: item[k] for k in keys})
    for key in genes[0].keys() & genes[1].keys(): assert genes[0][key] == genes[1][key]
    write_once(shadow / 'off-equivalence.json', {'status': 'PASS', 'paidSHA256': a['paidSHA256'],
        'allPaidSolutionsIdentical': True, 'searchAndDecoderCountsIdentical': True,
        'initialLedgerAndCommonCheckpointGenomesIdentical': True})

"""Paid-sequence equivalence first, then the preregistered empty-neighborhood engineering gate."""
from run_long_budget_bridge import read, rows, write_once
from center_task_checks import off_equivalence


def acceptance(baseline, out, limit):
    off_equivalence(baseline, out)
    receipt, = rows(out / 'run-receipt.jsonl'); evidence, = rows(out / 'candidate-redundancy.json')
    total = evidence['totals']; strata = evidence['strata']
    assert evidence['paidObservations'] == total['paid'] == limit
    assert evidence['uniqueWholePhysicalKeys'] + total.get('historyDuplicate', 0) == limit
    assert evidence['duplicateTimelineDigestsVerified'] == total.get('historyDuplicate', 0)
    assert total.get('certifiedEmptyNeighborhood', 0) <= total.get('parentIdentity', 0) <= total.get('historyDuplicate', 0)
    assert evidence['activeEvaluationCleared'] and evidence['pendingUnpaidProposals'] == 0
    for stage in ('initialization', 'global', 'inter', 'intra'):
        assert strata.get('stage:' + stage, {}).get('paid', 0) == receipt['search'].get(stage + '.evaluations', 0)
    assert sum(strata.get('operator:' + str(i), {}).get('paid', 0) for i in range(9)) == receipt['search']['intra.evaluations']
    for sample in evidence['samples']:
        assert sample['paidFE'] <= limit
        if sample['historyDuplicate']: assert sample['previousPaidFE'] < sample['paidFE']
    write_once(out / 'redundancy-acceptance.json', {'status': 'PASS', 'paidFE': limit,
        'allWholeDuplicatesFullTimelineVerified': evidence['duplicateTimelineDigestsVerified'],
        'allCertifiedEmptyProposalsActuallyParentIdentical': True,
        'completePaidSequenceUnchanged': True, 'noEvaluationSkipped': True})
    return evidence


def cell(stem, method, evidence):
    total = evidence['totals']; paid = total['paid']
    duplicate, identity, empty = [total.get(k, 0) for k in ('historyDuplicate', 'parentIdentity', 'certifiedEmptyNeighborhood')]
    return {'stem': stem, 'method': method, 'paidFE': paid, 'uniqueWholePhysicalKeys': evidence['uniqueWholePhysicalKeys'],
        'wholeHistoryDuplicateFE': duplicate, 'wholeHistoryDuplicateFraction': duplicate / paid,
        'intraParentIdentityFE': identity, 'intraParentIdentityFractionOfAllFE': identity / paid,
        'certifiedEmptyNeighborhoodFE': empty, 'certifiedEmptyFractionOfAllFE': empty / paid,
        'duplicatesBeyondIntraParentIdentity': duplicate - identity,
        'permitsEmptyNeighborhoodEngineering': empty / paid >= .05,
        'strata': evidence['strata'], 'costLimit': 'Observer-only run; neither overhead nor wall clock is efficacy evidence.'}


def finish(root, cells):
    eligible = all(c['permitsEmptyNeighborhoodEngineering'] for c in cells)
    result = {'cells': cells, 'worthEmptyNeighborhoodEngineering': eligible,
        'decision': 'SEPARATE_COMMON_OPERATOR_PRECHECK_PROTOCOL_ONLY' if eligible else 'STOP_EMPTY_NEIGHBORHOOD_HYPOTHESIS',
        'historyDuplicateSkippingAuthorized': False, 'algorithmImplemented': False, 'goalAchieved': False}
    write_once(root / 'analysis.json', result); return result

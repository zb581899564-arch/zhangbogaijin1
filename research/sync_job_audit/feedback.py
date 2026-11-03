"""Validate observational records and expose timing without inferring causal speedups."""
from research.semantic_repair.trials import json_lines


def validate_feedback(folder, summary, label, *, require_complete=True):
    limit = summary['timeLimitSeconds'] if summary['timeLimitSeconds'] is not None else float('inf')
    trace = json_lines(folder / 'feedback-trace.jsonl')
    data = summary['semanticAudit'].get('feedbackTiming')
    if not data or data.get('enabled') is not True or data.get('observationOnly') is not True:
        raise ValueError('Missing observation-only feedback provenance')
    if not trace or trace[0] != dict(data, type='feedback-summary'):
        raise ValueError('Feedback trace disagrees with summary')
    if data['successfulFE'] != summary['successful']:
        raise ValueError('Feedback stamping added or omitted paid successes')
    if data['externalArchiveAdmissions'] != summary['semanticAudit']['paidArchiveAdmissions']:
        raise ValueError('Feedback admission count uses a different deadline')
    if data['externalAdmissionSnapshotsInsertedByCutoff'] > data['externalAdmissionSnapshotsOfferedByCutoff']:
        raise ValueError('Insertion without an observed internal offer')
    if data['externalAdmissionSnapshotsOfferedByCutoff'] > data['externalArchiveAdmissions']:
        raise ValueError('Paid snapshot provenance was duplicated')
    complete = [row for row in trace[1:] if row['complete']]
    if len(complete) > 3 or len(trace) > 5:
        raise ValueError('Unbounded feedback capture')
    if label == 'NSGA':
        if trace[1:] or data['generationsStarted']:
            raise ValueError('NSGA unexpectedly acquired QGS feedback')
    elif require_complete and not complete:
        raise ValueError('No completed QGS generation')
    for frame in trace[1:]:
        seen = set()
        if frame['complete'] and frame['deadlineValid'] and frame['elapsedSeconds'] > limit:
            raise ValueError('Future generation marked valid')
        for step in frame['steps']:
            identity = step['direction'], step['step']
            if identity in seen or step['step'] not in (1, 10, 25, 50):
                raise ValueError('Duplicate or unregistered QGS timing sample')
            seen.add(identity)
            if step['successfulFE'] - step['archiveRefreshFE'] != step['archiveRefreshLagFE']:
                raise ValueError('Broken refresh age')
            if step['successfulFE'] - step['teacherPaidFE'] != step['teacherAgeFE']:
                raise ValueError('Broken teacher birth provenance')
            if step['archiveRefreshFE'] != frame['refreshAtStartFE']:
                raise ValueError('Internal archive refreshed inside the unchanged QGS phase')
            if step['teacherAgeFE'] < 0 or step['archiveRefreshLagFE'] < 0:
                raise ValueError('A teacher came from a future evaluation')
            if step['action'] == 2 and step['teacherPaidFE'] > step['archiveRefreshFE']:
                raise ValueError('Action2 teacher entered before the actual refresh')
    return trace


def feedback_records(run):
    identity = {key: run[key] for key in ('instance', 'seed', 'variant')}
    data = run['summary']['semanticAudit']['feedbackTiming']
    totals = identity | {key: value for key, value in data.items() if not isinstance(value, dict)}
    for key, value in data.items():
        if isinstance(value, dict):
            totals.update({key + '.' + field: item for field, item in value.items()})
    steps = []
    for frame in run['feedbackTrace'][1:]:
        for row in frame['steps']:
            steps.append(identity | {'generation': frame['generation'], 'completeGeneration': frame['complete'],
                         'generationDeadlineValid': frame['deadlineValid'], 'generationStartFE': frame['startFE'], **row})
    return totals, steps

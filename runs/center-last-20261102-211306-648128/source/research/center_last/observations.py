from research.semantic_repair.trials import json_lines
from research.sync_job_audit.feedback import validate_feedback
from .protocol import ORIGINAL, LAST


def validate_observations(folder, summary, label, *, require_complete=True):
    feedback = validate_feedback(folder, summary, 'NSGA' if label == 'NSGA' else label, require_complete=require_complete)
    if label == 'NSGA':
        if 'cooperation' in summary or 'alignedKernelProposals' in summary['search']: raise ValueError('NSGA acquired cooperation')
        return feedback, None
    co = summary['cooperation']; sharing = label.startswith('SHARE'); last = label.endswith('LAST')
    if co['sharing'] is not sharing or co['globalOrder'] != (LAST if last else ORIGINAL): raise ValueError('Wrong sharing/order factor')
    if summary['search'].get('globalKernel') != 'JOB_ALIGNED': raise ValueError('Kernel changed')
    if summary.get('mechanismCapture') or summary.get('retainInitialParents') or 'joint' in summary:
        raise ValueError('Unregistered strategy entered run')
    trace = json_lines(folder / 'composition-trace.jsonl'); data = co['compositionTiming']
    if not trace or trace[0] != dict(data, type='composition-summary') or len(trace) > 33: raise ValueError('Invalid bounded composition trace')
    if data['paidAssemblies'] != co.get('assembliesValidated', 0): raise ValueError('Missing paid composition')
    if not sharing and (data['paidAssemblies'] or co.get('assembliesProposed', 0) or co['poolRecords']): raise ValueError('SYNC shared')
    if not last and data['sameGenerationLateGroupFragments'] != 0: raise ValueError('Original order consumed future late-group source')
    complete_count = summary['search'].get('generations.completed', 0)
    for gen in data['perGeneration']:
        if gen['generation'] <= complete_count:
            if gen['eligibleCenterOpportunities'] != (400 if sharing else 0): raise ValueError('Full-generation composition frequency changed')
            if gen['paidAssemblies'] != gen['proposedAssemblies']: raise ValueError('Completed generation left an unpaid proposal')
    limit = summary['timeLimitSeconds'] if summary['timeLimitSeconds'] is not None else float('inf')
    for row in trace[1:]:
        if not row['deadlineValid'] or row['elapsedSeconds'] > limit: raise ValueError('Late composition credited')
        if row['paidFE'] != row['proposalFE'] + 1: raise ValueError('Composition added hidden FE')
        for fragment in row['fragments']:
            if fragment['paidFE'] > row['proposalFE'] or fragment['generation'] > row['generation']: raise ValueError('Future source')
            if fragment['ageFEAtProposal'] != row['proposalFE'] - fragment['paidFE']: raise ValueError('Wrong fragment age')
            if fragment['sameGeneration'] != (fragment['generation'] == row['generation']): raise ValueError('Wrong generation attribution')
    for frame in feedback[1:]:
        for step in frame['steps']:
            if step['direction'] == 'CENTER' and step['step'] == 1:
                if step['successfulFE'] - frame['startFE'] != (2250 if last else 750): raise ValueError('Global center position was not implemented')
    return feedback, trace


def composition_metrics(run):
    identity = {key: run[key] for key in ['instance', 'seed', 'variant']}
    if run['variant'] == 'NSGA': return None, [], []
    co = run['summary']['cooperation']; data = co['compositionTiming']
    total = identity | {key: value for key, value in data.items() if not isinstance(value, (dict, list))}
    total['eligibleCenterOpportunities'] = co['eligibleCenterOpportunities']
    total['assemblyRequests'] = co.get('assemblyRequests', 0); total['assembliesProposed'] = co.get('assembliesProposed', 0)
    total['completeGenerations'] = run['summary']['search'].get('generations.completed', 0)
    for key in ['fromProducer', 'sameGenerationFromProducer']:
        total.update({key + '.' + name: value for name, value in data[key].items()})
    generations = [identity | row | {'completeGeneration': row['generation'] <= total['completeGenerations']} for row in data['perGeneration']]
    samples = [identity | row for row in run['compositionTrace'][1:]]
    return total, generations, samples

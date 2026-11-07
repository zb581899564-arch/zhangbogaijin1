"""Complete-matrix descriptive attribution and feedback timing; zero schedule FE."""
import json
from pathlib import Path
import sys
import pandas as pd

root = Path(sys.argv[1]).resolve()
status = json.loads((root / 'final-status.json').read_text())
assert status['status'] == 'SYNC_JOB_AUDIT_COMPLETE' and status['completed'] == 120
analysis = root / status['analysis']; effects = json.loads((analysis / 'effects.json').read_text())
out = root / 'interpretation'; out.mkdir(exist_ok=False)
summary, instances = [], []
for label, record in effects.items():
    t = record['T']['1.5']; fe = record['FE15000']['allInstances']
    summary.append({'comparison': label, 'meanTPercent': t['mean_effect_percent'],
        'medianTPercent': t['median_effect_percent'], 'practicalWins': t['practical_wins'],
        'practicalLosses': t['practical_losses'], 'worstTPercent': t['worst_effect_percent'],
        'removeBestMeanTPercent': t['mean_after_removing_best_instance_percent'],
        'meanFE15000Percent': fe['mean_effect_percent'],
        'reference1.25MeanPercent': record['T']['1.25']['mean_effect_percent'],
        'reference2.0MeanPercent': record['T']['2.0']['mean_effect_percent']})
    lookup = {r['instance']: r for r in fe['instances']}
    for row in t['instances']:
        instances.append({'comparison': label, 'instance': row['instance'], 'effectTPercent': row['effect_percent'],
                          'effectFE15000Percent': lookup[row['instance']]['effect_percent']})
pd.DataFrame(summary).to_csv(out / 'comparison-summary.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(instances).to_csv(out / 'instance-effects.csv', index=False, encoding='utf-8-sig')
feedback = pd.read_csv(analysis / 'feedback-run-metrics.csv')
fields = ['externalArchiveAdmissions', 'externalAdmissionSnapshotsOfferedByCutoff',
          'externalAdmissionSnapshotsInsertedByCutoff', 'firstInsertionDelayFE.mean',
          'externalAdmissionFirstInsertionDelayFE.mean', 'action2TeacherAgeFE.mean']
feedback['externalAdmissionOfferFraction'] = feedback['externalAdmissionSnapshotsOfferedByCutoff'] / feedback['externalArchiveAdmissions']
feedback['externalAdmissionInsertionFraction'] = feedback['externalAdmissionSnapshotsInsertedByCutoff'] / feedback['externalArchiveAdmissions']
fields += ['externalAdmissionOfferFraction', 'externalAdmissionInsertionFraction']
feedback[feedback.variant != 'NSGA'].groupby(['instance', 'variant'])[fields].mean().reset_index().to_csv(
    out / 'feedback-by-instance.csv', index=False, encoding='utf-8-sig')
feedback[feedback.variant != 'NSGA'].groupby('variant')[fields].mean().to_csv(out / 'feedback-summary.csv', encoding='utf-8-sig')
steps = pd.read_csv(analysis / 'feedback-steps.csv')
complete = steps[steps.completeGeneration & steps.generationDeadlineValid]
group = complete.groupby(['instance', 'seed', 'variant', 'direction', 'step'])[
    ['archiveRefreshLagFE', 'teacherAgeFE']].mean().reset_index()
group.groupby(['variant', 'direction', 'step'])[['archiveRefreshLagFE', 'teacherAgeFE']].mean().reset_index().to_csv(
    out / 'complete-generation-step-timing.csv', index=False, encoding='utf-8-sig')
costs = pd.read_csv(analysis / 'run-metrics.csv')
costs['deadlineFEperSecond'] = costs.deadlineValidFE / costs.searchSeconds
costs['directAuditFraction'] = costs['semanticAudit.auditSeconds'] / costs.searchSeconds
costs.groupby(['instance', 'variant'])[['deadlineFEperSecond', 'directAuditFraction']].mean().reset_index().to_csv(
    out / 'costs-by-instance.csv', index=False, encoding='utf-8-sig')
audit = json.loads((analysis / 'audit.json').read_text())
(out / 'receipt.json').write_text(json.dumps(audit | {'mainCampaignSeconds': status['wallSeconds'],
    'postAnalysisExtraFE': 0, 'scope': 'Observed snapshot delays; no timing intervention and no performance causality claim'},
    ensure_ascii=False, indent=2), encoding='utf-8')
# Invariance check on existing FE checkpoint data; historical wall-time scores are not reused.
previous = root.parent / 'job-aligned-closure-20261102-174433-417375'
matched = []
for current in (root / 'trials/audit').rglob('anytime.jsonl'):
    label = current.parent.name
    if label not in ('SO_JOB', 'SHARE_JOB', 'NSGA'): continue
    relative = current.relative_to(root / 'trials/audit')
    old = previous / 'trials/closure' / relative
    def fe_front(path):
        values = [json.loads(line) for line in path.read_text().splitlines()]
        rows = [r for r in values if r['checkpointKind'] == 'FE' and r['checkpoint'] == 15000]
        assert len(rows) == 1 and rows[0].get('reached', True)
        return rows[0]['front']
    assert fe_front(current) == fe_front(old), str(relative)
    matched.append(str(relative))
assert len(matched) == 90
(out / 'control-fe-invariance.json').write_text(json.dumps({'status': 'PASS', 'controls': 90,
    'checkpoint': 15000, 'frontsExactlyEqual': True, 'extraFE': 0, 'cells': matched},
    ensure_ascii=False, indent=2), encoding='utf-8')
print(pd.DataFrame(summary).to_string(index=False))
print('INTERPRETATION_COMPLETE', out)

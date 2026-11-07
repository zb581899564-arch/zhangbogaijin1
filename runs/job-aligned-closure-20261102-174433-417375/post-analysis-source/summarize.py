"""Read-only numerical summaries of a completed frozen matrix; writes a new interpretation folder."""
import json
from pathlib import Path
import sys
import pandas as pd

root = Path(sys.argv[1]).resolve()
status = json.loads((root / 'final-status.json').read_text(encoding='utf-8'))
assert status['status'] == 'JOB_ALIGNED_CLOSURE_COMPLETE' and status['completed'] == 150
analysis = root / status['analysis']
effects = json.loads((analysis / 'effects.json').read_text(encoding='utf-8'))
audit = json.loads((analysis / 'audit.json').read_text(encoding='utf-8'))
assert audit['runs'] == 150 and audit['genuineFailures'] == 0
out = root / 'interpretation'; out.mkdir(exist_ok=False)
rows, instance_rows = [], []
for label, result in effects.items():
    primary = result['T']['1.5']; fixed = result['FE15000']['allInstances']
    rows.append({'comparison': label, 'meanTPercent': primary['mean_effect_percent'],
        'medianTPercent': primary['median_effect_percent'], 'practicalWins': primary['practical_wins'],
        'practicalLosses': primary['practical_losses'], 'worstTPercent': primary['worst_effect_percent'],
        'removeBestInstanceMeanTPercent': primary['mean_after_removing_best_instance_percent'],
        'meanFE15000Percent': fixed['mean_effect_percent'],
        'reference1.25MeanPercent': result['T']['1.25']['mean_effect_percent'],
        'reference2.0MeanPercent': result['T']['2.0']['mean_effect_percent'],
        'exploratoryInterval95': result['uncertainty'].get('mean_effect_percent_interval95')})
    fixed_lookup = {r['instance']: r for r in fixed['instances']}
    for item in primary['instances']:
        instance_rows.append({'comparison': label, 'instance': item['instance'],
            'effectTPercent': item['effect_percent'],
            'effectFE15000Percent': fixed_lookup[item['instance']]['effect_percent']})
pd.DataFrame(rows).to_csv(out / 'comparison-summary.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(instance_rows).to_csv(out / 'instance-effects.csv', index=False, encoding='utf-8-sig')
costs = pd.read_csv(analysis / 'run-metrics.csv')
costs['deadlineFEperSecond'] = costs['deadlineValidFE'] / costs['searchSeconds']
additional = []
for p in (root / 'trials').rglob('summary.json'):
    summary = json.loads(p.read_text(encoding='utf-8'))
    identity = {'instance': p.parents[2].name, 'seed': summary['seed'], 'variant': p.parent.name}
    decoder = summary['decoder']
    reused, recomputed = decoder['dynamic.reusedOperations'], decoder['dynamic.recomputedOperations']
    additional.append(identity | {'operationReuseFraction': reused / (reused + recomputed),
        'globalPaidFE': summary['semanticAudit'].get('paid.global', 0),
        'interPaidFE': summary['semanticAudit'].get('paid.inter', 0),
        'intraPaidFE': summary['semanticAudit'].get('paid.intra', 0),
        'sharedAssembliesPaid': summary.get('cooperation', {}).get('assembliesValidated', 0)})
costs = costs.merge(pd.DataFrame(additional), on=['instance', 'seed', 'variant'], validate='one_to_one')
costs['directAuditFraction'] = costs['semanticAudit.auditSeconds'] / costs['searchSeconds']
fields = ['deadlineFEperSecond', 'decodeSeconds', 'operationReuseFraction', 'directAuditFraction',
          'globalPaidFE', 'interPaidFE', 'intraPaidFE', 'alignedKernelProposals', 'sharedAssembliesPaid']
per_instance = costs.groupby(['instance', 'variant'])[fields].mean().reset_index()
per_instance.to_csv(out / 'costs-by-instance.csv', index=False, encoding='utf-8-sig')
per_instance.groupby('variant')[fields].mean().to_csv(out / 'cost-summary.csv', encoding='utf-8-sig')
(out / 'receipt.json').write_text(json.dumps({'status': 'COMPLETE', 'runs': 150,
    'mainCampaignSeconds': status['wallSeconds'], 'searchSuccessfulFE': audit['successfulFE'],
    'returnedSolutionsReplayed': audit['offlineReturnedSolutionReplays'], 'fixedFEReached': audit['fixedFEReached'],
    'genuineFailures': 0, 'postAnalysisExtraFE': 0, 'formalStep6Started': False,
    'scope': 'Closed-loop development effects; operation reuse and stage allocation are descriptive, not isolated causal effects'},
    ensure_ascii=False, indent=2), encoding='utf-8')
print(pd.DataFrame(rows).to_string(index=False))
print('POST_ANALYSIS_COMPLETE', out)

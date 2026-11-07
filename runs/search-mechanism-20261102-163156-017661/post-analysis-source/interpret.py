"""Reproducible descriptive interpretation; no schedule evaluations or optimizer calls."""
import json
from pathlib import Path
import sys
import pandas as pd

root = Path(sys.argv[1]).resolve()
analysis = root / json.loads((root / 'status.json').read_text())['analysis']
batches = pd.read_csv(analysis / 'kernel-paid-batches.csv')
retention = pd.read_csv(analysis / 'retention-generations.csv')
out = root / 'interpretation'
out.mkdir(exist_ok=False)
tables = []
for (origin, phase), data in batches.groupby(['origin', 'phase']):
    per_instance = data.groupby(['instance', 'kernel']).agg(
        gain=('batchDeltaHV', 'mean'), seconds=('generationEvaluationSeconds', 'mean')).reset_index()
    quality = per_instance.pivot(index='instance', columns='kernel', values='gain')
    costs = per_instance.pivot(index='instance', columns='kernel', values='seconds')
    for kernel in ['JOB_ALIGNED', 'CLASSIC_GLOBAL', 'CLASSIC_PERSONAL']:
        control = quality.PAPER.mean()
        candidate = quality[kernel].mean()
        control_cost, candidate_cost = costs.PAPER.mean(), costs[kernel].mean()
        tables.append({'origin': origin, 'phase': phase, 'kernel': kernel,
            'paidCandidatesPerBatch': 8, 'instances': len(quality),
            'paperBatchDeltaHV': control, 'candidateBatchDeltaHV': candidate,
            'relativeBatchGainPercent': 100 * (candidate / control - 1),
            'positiveInstances': int((quality[kernel] > quality.PAPER).sum()),
            'negativeInstances': int((quality[kernel] < quality.PAPER).sum()),
            'paperBatchSeconds': control_cost, 'candidateBatchSeconds': candidate_cost,
            'relativeCostPercent': 100 * (candidate_cost / control_cost - 1),
            'scope': 'Equal8FE fixed-parent batch delta, not whole-algorithm HV; measured microcost, not a matched wall-time search'})
pd.DataFrame(tables).to_csv(out / 'matched-eight-FE-batches.csv', index=False, encoding='utf-8-sig')
columns = ['parentNDUncoveredByGLFraction', 'parentNDGenotypeSurvivalSelectedFraction',
           'GLNDCoveredBySelectedFraction', 'offlineOracleParentGainPercentOfGL']
per_run = retention.groupby(['instance', 'seed', 'variant'])[columns].mean().reset_index()
per_instance = per_run.groupby(['instance', 'variant'])[columns].mean().reset_index()
h1 = per_instance.groupby('variant')[columns].mean().reset_index()
h1.to_csv(out / 'retention-instance-balanced.csv', index=False, encoding='utf-8-sig')
summaries = [json.loads(p.read_text()) for p in (root / 'trials').rglob('summary.json')]
probes = json.loads((root / 'kernel-receipts.json').read_text())
receipt = {'status': 'COMPLETE', 'performanceRuns': len(summaries),
    'searchSuccessfulFE': sum(row['successful'] for row in summaries),
    'searchAttemptedFE': sum(row['attempted'] for row in summaries),
    'genuineSearchFailures': sum(row['failed'] - row['timeInterruptedAttempts'] for row in summaries),
    'searchArchiveOfflineReplays': sum(row['offlineValidationDecodes'] for row in summaries),
    'maxDeadlineOvershootSeconds': max(row['deadlineOvershootSeconds'] for row in summaries),
    'probeCases': sum(row['cases'] for row in probes),
    'probeCandidateFE': sum(row['candidateFE'] for row in probes),
    'probeParentReplayFE': sum(row['parentReplayFE'] for row in probes),
    'probeOfflineCandidateReplays': sum(row['offlineCandidateReplays'] for row in probes),
    'probeFailures': sum(row['failedFE'] for row in probes),
    'closureBranch': 'SKIPPED_PREDECLARED_GATE_NOT_MET', 'newOptimizerVariantsPerformanceRun': False,
    'postAnalysisExtraFE': 0, 'formalStep6Started': False}
(out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False, indent=2))

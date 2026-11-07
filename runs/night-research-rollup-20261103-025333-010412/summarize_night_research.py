"""Roll up completed, predeclared night outputs; never rerun or reclassify a search."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.semantic_repair.evidence import read, write_once


def campaign(folder):
    root = Path(folder).resolve()
    final, protocol = read(root / 'final-status.json'), read(root / 'protocol.json')
    if final['status'] != 'NIGHT_CAMPAIGN_COMPLETE' or final['completed'] != protocol['runs']:
        raise ValueError('Only a complete original campaign may enter the rollup')
    analysis = root / final['analysis']
    audit, decision = read(analysis / 'audit.json'), read(analysis / 'decision.json')
    if audit['runs'] != protocol['runs'] or audit['genuineFailures'] != 0:
        raise ValueError('Incomplete or failed matrix')
    effects = read(analysis / 'effects.json')
    comparisons = {}
    for role, control in decision['control_mapping'].items():
        effect = effects[protocol['candidate'] + '__vs__' + control]
        comparisons[role] = {'control': control, 'T': effect['T']['1.5'],
            'FE15000': effect['FE15000']['allInstances'], 'IGDplus': effect['IGDplus']}
    renewal = []
    for path in (root / 'trials').rglob('summary.json'):
        summary = read(path)
        observation = summary.get('cooperation', {}).get('contextRenewal')
        if observation:
            renewal.append({'searchMode': summary['mode'], **observation})
    return {'root': str(root), 'analysis': str(analysis), 'hypothesis': protocol['hypothesis'],
        'candidate': protocol['candidate'], 'seeds': protocol['algorithm_seeds'], 'decision': decision,
        'comparisons': comparisons, 'interactions': read(analysis / 'interactions.json'),
        'audit': audit, 'wallSeconds': final['wallSeconds'], 'contextRenewalOwners': renewal,
        'transfer': read(analysis / 'factory-transfer-summary.json')
            if (analysis / 'factory-transfer-summary.json').exists() else None,
        'engineeringManifest': read(root / 'engineering-source-manifest.json'),
        'instances': protocol['instances']}


def engineering(folder):
    root = Path(folder).resolve()
    acceptance = read(root / 'acceptance.json')
    if acceptance['status'] != 'passed':
        raise ValueError('Engineering is not accepted')
    rows = [read(path) for name in ('integration', 'frozen-control', 'loader-smoke')
        for path in (root / name).rglob('summary.json')]
    return {'root': str(root), 'realEntryChecks': len(acceptance['realEntryChecks']),
        'originalControlByteExactChecks': sum(r['originalControlByteExact'] for r in acceptance['realEntryChecks']),
        'ownedOptimizerRunsIncludingReferencesAndTimeSmoke': len(rows),
        'successfulOptimizerFE': sum(r['successful'] for r in rows),
        'returnedReplayDecodes': sum(r['offlineValidationDecodes'] for r in rows),
        'checkpointReplayDecodes': sum(r.get('checkpointEvidence', {}).get('uniqueOfflineDecodes', 0) for r in rows),
        'nightCooperationChecksSyntheticDecoderCalls': 12, 'performanceEvidence': False,
        'scope': 'Engineering FE and synthetic fixture calls are separate from the two performance matrices'}


def rollup(args):
    stages = [campaign(args.h1), campaign(args.h2)]
    if [s['hypothesis'] for s in stages] != ['H1', 'H2']:
        raise ValueError('Expected the two separately frozen hypotheses')
    if stages[0]['engineeringManifest'] != stages[1]['engineeringManifest'] or stages[0]['instances'] != stages[1]['instances']:
        raise ValueError('The two matrices did not use the same accepted Java and inputs')
    if set(stages[0]['seeds']) & set(stages[1]['seeds']):
        raise ValueError('The two new seed sets overlap')
    fields = ('runs', 'successfulFE', 'attemptedFE', 'timeInterruptedAttempts', 'genuineFailures',
        'returnedSolutionsReplayed', 'offlineCheckpointValidationDecodes', 'checkpointCoveredPoints',
        'checkpointSearchCaptureSecondsIncludedInT', 'offlineCheckpointValidationSeconds',
        'processWallSeconds', 'controllerValidationSeconds')
    totals = {key: sum(stage['audit'][key] for stage in stages) for key in fields}
    totals['campaignWallSeconds'] = sum(stage['wallSeconds'] for stage in stages)
    totals['allFixedFEReached'] = all(s['audit']['fixedFEReached'] == s['audit']['runs'] for s in stages)
    output = ROOT / 'runs' / datetime.now().strftime('night-research-rollup-%Y%m%d-%H%M%S-%f')
    output.mkdir()
    write_once(output / 'rollup.json', {'status': 'COMPLETE', 'totals': totals, 'stages': stages,
        'engineering': engineering(args.engineering), 'newSearchFE': 0, 'newDecodeFE': 0,
        'scope': 'Descriptive rollup of completed predeclared analyses; no new thresholds or pooled H1/H2 quality estimate'})
    print(json.dumps({'output': str(output), 'totals': totals}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('h1', 'h2', 'engineering'):
        parser.add_argument('--' + name, type=Path, required=True)
    rollup(parser.parse_args())

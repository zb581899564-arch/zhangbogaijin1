"""Engineering checks for the single preregistered cap-deficit local-factory rule."""
from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dynamic_build import build_dynamic
from verify_cooperation_roles import validate_roles
from research.semantic_repair.evidence import read, write_once, digest
from research.semantic_repair.diagnostics import validate_trace
from verify_semantic_repair import validate_pool_scores

PREVIOUS = ROOT / 'runs/cooperation-roles-20261102-231315-641007'
INPUTS = PREVIOUS / 'inputs'
VARIANTS = {
    'SHARE_SPECIAL': {'mode': 'SHARE_JOB_ALIGNED', 'profile': 'SO'},
    'SHARE_DEMAND_SPECIAL': {'mode': 'SHARE_JOB_ALIGNED_DEMAND', 'profile': 'SO'},
    'SHARE_SHAM_SPECIAL': {'mode': 'SHARE_JOB_ALIGNED_SHAM', 'profile': 'SO'},
}


def validate_demand(folder, summary, label):
    if label == 'SHARE_SPECIAL':
        assert 'demandFeedback' not in summary['cooperation']
        assert not (folder / 'demand-trace.jsonl').exists()
        return
    expected = 'DEMAND' if label == 'SHARE_DEMAND_SPECIAL' else 'SHAM'
    data = summary['cooperation']['demandFeedback']
    assert data['mode'] == expected and data['extraFE'] == data['extraRNG'] == 0
    assert data['actionableQueries'] + data['resolvedOrNoGapQueries'] == data['eligibleQueries'] <= data['queries']
    assert data['routedOverrides'] <= data['actionableQueries']
    if expected == 'SHAM':
        assert data['routedOverrides'] == 0
    rows = [json.loads(x) for x in (folder / 'demand-trace.jsonl').read_text(encoding='utf-8').splitlines()]
    assert rows[0] == dict(data, type='demand-feedback-summary') and len(rows) <= 17
    for row in rows[1:]:
        deficits = [(c - row['cap']) / row['cap'] for c in row['factoryMinC']]
        largest = max(deficits)
        target = deficits.index(largest) if largest > 0 else -1
        assert target == row['targetFactory']
        selected = target if expected == 'DEMAND' and target >= 0 else row['randomFactory']
        assert row['selectedFactory'] == selected
        assert row['physicalGroup'] == 'MAKESPAN' and 0 <= row['family'] < 4
        assert row['requestFE'] <= row['queryFE'] <= summary['successful']


def real_entry(build, folder, stem, label, frozen=False, seconds='Infinity', fe=20000):
    folder.mkdir(parents=True); spec = VARIANTS[label]
    cp = ((PREVIOUS if frozen else build) / 'classpath.txt').read_text(encoding='utf-8').strip()
    data = INPUTS / stem
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.DynamicRun',
        str(data / (stem + '.txt')), str(data / 'RECONSTRUCTED-setup.txt'), str(data / 'fatigue-input.txt'), str(folder),
        spec['mode'], str(fe), '4242421', str(seconds), '1.0', 'true', 'false', '0', 'true', 'SCREEN', '0',
        spec['profile'], 'true', 'false', 'false', 'true', 'true']
    write_once(folder / 'command.json', cmd)
    with (folder / 'run.log').open('x', encoding='utf-8') as stream:
        result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
    if result.returncode:
        raise RuntimeError((folder / 'run.log').read_text(encoding='utf-8', errors='replace')[-3000:])
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['failed'] == summary['timeInterruptedAttempts']
    assert summary['archiveSize'] == summary['offlineValidationDecodes']
    if seconds == 'Infinity':
        assert summary['successful'] == summary['attempted'] == fe
    rows = [json.loads(x) for x in (folder / 'semantic-trace.jsonl').read_text(encoding='utf-8').splitlines()]
    validate_trace(rows, summary['semanticAudit'], summary); validate_pool_scores(rows)
    validate_roles(folder, summary, label, require_complete=seconds == 'Infinity')
    validate_demand(folder, summary, label)
    return summary


def verify():
    output = ROOT / 'runs' / datetime.now().strftime('demand-feedback-engineering-%Y%m%d-%H%M%S-%f')
    output.mkdir(); cp = build_dynamic(output, skip_maven=True)
    (output / 'classpath.txt').write_text(cp, encoding='utf-8')
    with (output / 'DemandFeedbackChecks.log').open('x', encoding='utf-8') as stream:
        result = subprocess.run(['java', '-Xmx768m', '-cp', cp,
            'org.uma.jmetal.util.research.cooperation.DemandFeedbackChecks'], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
    if result.returncode:
        raise RuntimeError((output / 'DemandFeedbackChecks.log').read_text(encoding='utf-8'))
    checks = []
    for stem in ['20_2_3_1', '200_8_5_1']:
        for label in VARIANTS:
            target = output / 'integration' / stem / label
            summary = real_entry(output, target, stem, label)
            if label == 'SHARE_SPECIAL':
                frozen = output / 'frozen-control' / stem / label
                real_entry(output, frozen, stem, label, frozen=True)
                assert (target / 'solutions.jsonl').read_bytes() == (frozen / 'solutions.jsonl').read_bytes()
            elif summary['cooperation']['demandFeedback']['eligibleQueries'] < 1:
                raise ValueError('New demand branch never reached local search')
            checks.append({'instance': stem, 'variant': label, 'FE': summary['successful'], 'originalControlByteExact': label == 'SHARE_SPECIAL'})
            print('DEMAND_ENTRY_PASS', stem, label, flush=True)
    for label in VARIANTS:
        real_entry(output, output / 'interruptions' / label, '20_2_3_1', label, seconds=.3, fe=9223372036854775807)
    write_once(output / 'source-manifest.json', {str(p.relative_to(ROOT)): digest(p)
        for folder in ['src/java', 'src/algorithms'] for p in (ROOT / folder).rglob('*.java')})
    write_once(output / 'acceptance.json', {'status': 'passed', 'realEntryChecks': checks,
        'originalControlMatchesFrozen': True, 'fixedDeficitRoutingAndShamVerified': True,
        'physicalScopeAndOriginalRandomDrawPreserved': True, 'poolAndQuotaReplay': True,
        'timeInterruptions': list(VARIANTS), 'qualitySelectedParameters': False})
    print('DEMAND_FEEDBACK_ENGINEERING_ACCEPTED', output, flush=True)


if __name__ == '__main__':
    verify()

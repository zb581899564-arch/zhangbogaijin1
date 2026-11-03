"""Necessary acceptance for uniform target preference and paid retained-pool observations."""
from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dynamic_build import build_dynamic
from verify_semantic_repair import validate_pool_scores
from research.semantic_repair.evidence import read, write_once, digest
from research.semantic_repair.diagnostics import validate_trace
from research.center_last.observations import validate_observations

PREVIOUS = ROOT / 'runs/center-last-20261102-211306-648128'
INPUTS = ROOT / 'runs/semantic-repair-20261102-130342-703425/inputs'
VARIANTS = {
    'SYNC_SPECIAL': {'mode': 'SYNC_JOB_ALIGNED', 'profile': 'SO'},
    'SYNC_UNIFORM': {'mode': 'SYNC_JOB_ALIGNED_UNIFORM', 'profile': 'SO'},
    'SHARE_SPECIAL': {'mode': 'SHARE_JOB_ALIGNED', 'profile': 'SO'},
    'SHARE_UNIFORM': {'mode': 'SHARE_JOB_ALIGNED_UNIFORM', 'profile': 'SO'},
    'NSGA': {'mode': 'NSGA2_4V', 'profile': 'V2'},
}


def validate_roles(folder, summary, label, require_complete=True):
    validate_observations(folder, summary, label, require_complete=require_complete)
    if label == 'NSGA':
        return
    uniform = label.endswith('UNIFORM')
    co = summary['cooperation']
    assert co['targetSpecialization'] is not uniform
    for name, gid in [('MAKESPAN', 1), ('CENTER', 2), ('ENERGY', 3), ('WORKER_COST', 4)]:
        pref = 'CENTER' if uniform else name
        assert co['rolePreferenceMap'][name] == pref
        assert summary['search'].get(f'qgs.g{gid}.preference.{pref}', 0) == summary['search'].get(f'qgs.g{gid}.updates', 0)
        if require_complete:
            assert summary['search'][f'local.g{gid}.preference.{pref}'] > 0
    rows = [json.loads(x) for x in (folder / 'cooperation-evidence.jsonl').read_text(encoding='utf-8').splitlines()]
    assert rows[0] == dict(co['poolEvidence'], type='cooperation-evidence-summary') and len(rows) <= 17
    assert co['poolEvidence']['extraFE'] == 0 and co['poolEvidence']['consumesRNG'] is False
    if label.startswith('SYNC'):
        assert rows[0]['requests'] == 0
    for row in rows[1:]:
        assert row['deadlineValid'] and row['proposalFE'] <= summary['successful']
        for factory in row['factories']:
            assert len(factory['records']) <= 8
            for record in factory['records']:
                assert 0 < record['paidFE'] <= row['proposalFE']


def real_entry(build, folder, stem, label, frozen=False, seconds='Infinity', fe=20000):
    folder.mkdir(parents=True)
    spec = VARIANTS[label]
    cp = ((PREVIOUS if frozen else build) / 'classpath.txt').read_text(encoding='utf-8').strip()
    data = INPUTS / stem
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.DynamicRun',
           str(data / (stem + '.txt')), str(data / 'RECONSTRUCTED-setup.txt'), str(data / 'fatigue-input.txt'), str(folder),
           spec['mode'], str(fe), '4242421', str(seconds), '1.0', 'true', 'false', '0', 'true', 'SCREEN', '0',
           spec['profile'], 'true', 'false', 'false', 'true', 'true']
    write_once(folder / 'command.json', cmd)
    with (folder / 'run.log').open('x', encoding='utf-8') as log:
        completed = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if completed.returncode:
        raise RuntimeError((folder / 'run.log').read_text(encoding='utf-8', errors='replace')[-3000:])
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['failed'] == summary['timeInterruptedAttempts']
    assert summary['archiveSize'] == summary['offlineValidationDecodes']
    if seconds == 'Infinity':
        assert summary['successful'] == summary['attempted'] == fe
    trace = [json.loads(x) for x in (folder / 'semantic-trace.jsonl').read_text(encoding='utf-8').splitlines()]
    validate_trace(trace, summary['semanticAudit'], summary)
    validate_pool_scores(trace)
    if not frozen:
        validate_roles(folder, summary, label, require_complete=summary['stopReason'] == 'FE_LIMIT')
    return summary


def verify():
    output = ROOT / 'runs' / datetime.now().strftime('cooperation-roles-engineering-%Y%m%d-%H%M%S-%f')
    output.mkdir()
    cp = build_dynamic(output, skip_maven=True)
    (output / 'classpath.txt').write_text(cp, encoding='utf-8')
    for name in ['CooperationRolesChecks', 'CompositionTimingChecks']:
        with (output / (name + '.log')).open('x', encoding='utf-8') as log:
            result = subprocess.run(['java', '-Xmx768m', '-cp', cp,
                'org.uma.jmetal.util.research.cooperation.' + name], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=60)
        if result.returncode:
            raise RuntimeError((output / (name + '.log')).read_text(encoding='utf-8'))
        print(name, 'PASS', flush=True)
    checks = []
    for stem in ['20_2_3_1', '200_8_5_1']:
        for label in VARIANTS:
            target = output / 'integration' / stem / label
            summary = real_entry(output, target, stem, label)
            control = label in ('SYNC_SPECIAL', 'SHARE_SPECIAL', 'NSGA')
            if control:
                reference = output / 'frozen-control' / stem / label
                real_entry(output, reference, stem, label, frozen=True)
                assert (target / 'solutions.jsonl').read_bytes() == (reference / 'solutions.jsonl').read_bytes()
            checks.append({'instance': stem, 'variant': label, 'FE': summary['successful'], 'frozenControlByteExact': control})
            print('ROLES_ENTRY_PASS', stem, label, flush=True)
    for label in VARIANTS:
        real_entry(output, output / 'interruptions' / label, '20_2_3_1', label, seconds=.3, fe=9223372036854775807)
    manifest = {str(p.relative_to(ROOT)): digest(p) for folder in ['src/java', 'src/algorithms'] for p in (ROOT / folder).rglob('*.java')}
    write_once(output / 'source-manifest.json', manifest)
    write_once(output / 'acceptance.json', {'status': 'passed', 'realEntryChecks': checks,
        'physicalGroupsAndQuotasRetained': True, 'uniformPreferencesVerified': True, 'originalControlsMatchFrozen': True,
        'poolObservationFEAndRNGZero': True, 'boundedPaidPoolProvenance': True, 'timeInterruptions': list(VARIANTS),
        'qualitySelectedParameters': False})
    print('COOPERATION_ROLES_ENGINEERING_ACCEPTED', output, flush=True)


if __name__ == '__main__':
    verify()

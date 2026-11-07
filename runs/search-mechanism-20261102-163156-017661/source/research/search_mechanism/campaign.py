"""One-JVM diagnostic campaign, immutable owners and a single original wall clock."""
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from research.semantic_repair.evidence import read, write_once, status, _freeze_classpath, digest
from research.semantic_repair.execution import CampaignDeadline, controller_lock
from research.semantic_repair.trials import json_lines
from .protocol import ROOT, PREVIOUS, make_protocol, jobs
from .analysis import _load_trial
from .retention import generation_metrics, retention_gate


def prepare(engineering):
    engineering = Path(engineering).resolve()
    if read(engineering / 'acceptance.json')['status'] != 'passed':
        raise ValueError('Engineering acceptance missing')
    root = ROOT / 'runs' / datetime.now().strftime('search-mechanism-%Y%m%d-%H%M%S-%f')
    root.mkdir()
    write_once(root / 'clock.json', {'startedEpoch': time.time(), 'wallCapSeconds': 5400})
    protocol = make_protocol(read(PREVIOUS / 'protocol.json'))
    write_once(root / 'protocol.json', protocol)
    write_once(root / 'engineering-acceptance.json', read(engineering / 'acceptance.json'))
    for row in protocol['instances']:
        shutil.copytree(PREVIOUS / 'inputs' / row['stem'], root / 'inputs' / row['stem'])
    _freeze_classpath(engineering, root)
    manifest = {}
    for folder in ['src/java', 'src/algorithms', 'research/search_mechanism']:
        for p in (ROOT / folder).rglob('*'):
            if p.suffix not in ('.java', '.py'):
                continue
            target = root / 'source' / p.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, target)
            manifest[str(p.relative_to(ROOT))] = digest(target)
    write_once(root / 'source-manifest.json', manifest)
    status(root, {'status': 'PREPARED', 'completed': 0, 'maximumRuns': 90})
    return root


def _execute(root, folder, command, deadline, expected_seconds):
    if folder.exists():
        raise RuntimeError('Owner already exists; will not rerun: ' + str(folder))
    deadline.require(expected_seconds + 5)
    folder.mkdir(parents=True)
    write_once(folder / 'command.json', command)
    start = time.monotonic()
    with (folder / 'run.log').open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                timeout=min(deadline.remaining(), max(150., expected_seconds * 3 + 30)))
    write_once(folder / 'execution.json', {'processWallSeconds': time.monotonic() - start, 'returncode': result.returncode})
    if result.returncode:
        raise RuntimeError('Owned JVM failed; log preserved: ' + str(folder))
    deadline.require()


def _run_search(root, protocol, job, deadline):
    folder = root / 'trials' / job['phase'] / job['instance'] / str(job['seed']) / job['variant']
    spec = protocol['variants'][job['variant']]
    inputs = root / 'inputs' / job['instance']
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', (root / 'classpath.txt').read_text(encoding='utf-8'),
           'research.dynamic.DynamicRun', str(inputs / (job['instance'] + '.txt')),
           str(inputs / 'RECONSTRUCTED-setup.txt'), str(inputs / 'fatigue-input.txt'), str(folder),
           spec['mode'], '9223372036854775807', str(job['seed']), str(job['seconds']),
           '1.0', 'true', 'false', '0', 'true', 'SCREEN', '0', spec['profile'], 'true', 'true', str(spec['parents']).lower()]
    _execute(root, folder, cmd, deadline, job['seconds'])
    instance = next(row for row in protocol['instances'] if row['stem'] == job['instance'])
    return _load_trial(folder, instance, job['seed'], job['variant'], spec)


def _case_fields(case):
    parent = case['parent']; family = parent.get('family')
    family = -1 if family is None else family
    fixed = parent.get('fixedFactoryByJob')
    csv = lambda values: ','.join(str(value) for value in values)
    out = [case['caseId'], str(family), '-' if fixed is None else csv(fixed)]
    for field in ['parent', 'personal', 'global']:
        value = case[field]
        out.extend(csv(value[key]) for key in ['JS', 'FA', 'MA', 'WA', 'objectives'])
    assert len(out) == 18
    return '\t'.join(out)


def run_probe(root, protocol, run, index, deadline):
    cases = [row for row in run['trace'] if row['type'] == 'kernel-case']
    if not cases:
        raise ValueError('No paid parent snapshots for registered probe owner')
    inputs = root / 'inputs' / run['instance']
    tsv = root / 'probe-inputs' / (str(index) + '.tsv'); tsv.parent.mkdir(exist_ok=True)
    with tsv.open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(_case_fields(case) for case in cases) + '\n')
    folder = root / 'probes' / run['instance'] / str(run['seed']) / run['variant']
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', (root / 'classpath.txt').read_text(encoding='utf-8'),
           'research.dynamic.KernelProbeRun', str(inputs / (run['instance'] + '.txt')),
           str(inputs / 'RECONSTRUCTED-setup.txt'), str(inputs / 'fatigue-input.txt'), str(tsv),
           str(folder), str(protocol['kernel_replicates']), str(910000000 + index * 10000)]
    _execute(root, folder, cmd, deadline, 10)
    receipt = read(folder / 'kernel-receipt.json')
    assert receipt['status'] == 'passed' and receipt['cases'] == len(cases)
    assert receipt['candidateFE'] == len(cases) * 4 * protocol['kernel_replicates']
    lookup = {row['caseId']: row for row in cases}
    records = []
    for row in json_lines(folder / 'kernel-raw.jsonl'):
        case = lookup[row['caseId']]
        records.append({'phase': case['phase'], 'sourceSuccessfulFE': case['successfulFE'], 'instance': run['instance'],
                        'origin': run['variant'], 'sourceSeed': run['seed'], **row})
    return records, receipt


def campaign(engineering):
    root = prepare(engineering); deadline = CampaignDeadline(root)
    print('SEARCH_MECHANISM_ROOT', root, flush=True)
    protocol = read(root / 'protocol.json'); runs, h1 = [], []
    with controller_lock(root):
        for job in jobs(protocol, 'capture'):
            run = _run_search(root, protocol, job, deadline); runs.append(run)
            instance = next(row for row in protocol['instances'] if row['stem'] == job['instance'])
            for generation in run['generations']:
                h1.append({key: run[key] for key in ['instance', 'seed', 'variant']} |
                          generation_metrics(generation, instance['normalization']))
            status(root, {'status': 'CAPTURE_RUNNING', 'completed': len(runs), 'maximumRuns': 90})
            print('CAPTURE', len(runs), '/54', job['instance'], job['variant'], flush=True)
        gate = retention_gate(h1, protocol['instances'])
        if gate['status'] != 'RESOLVED':
            raise ValueError('Retention gate unresolved')
        write_once(root / 'closure-decision.json', gate)
        phases = ['capture']
        if gate['triggered']:
            phases.append('closure')
            for i, job in enumerate(jobs(protocol, 'closure'), 1):
                _run_search(root, protocol, job, deadline)
                status(root, {'status': 'CLOSURE_RUNNING', 'completed': 54 + i, 'maximumRuns': 90})
                print('CLOSURE', i, '/36', job['instance'], job['variant'], flush=True)
        kernel_receipts = []
        with (root / 'case-snapshots.jsonl').open('x', encoding='utf-8') as snapshots:
            for run in runs:
                for row in run['trace']:
                    if row['type'] == 'kernel-case':
                        snapshots.write(json.dumps({**row, 'instance': run['instance'], 'origin': run['variant'],
                                                    'sourceSeed': run['seed']}, ensure_ascii=False, allow_nan=False) + '\n')
        with (root / 'kernel-results.jsonl').open('x', encoding='utf-8') as output:
            for index, run in enumerate(runs):
                records, receipt = run_probe(root, protocol, run, index, deadline)
                for row in records:
                    output.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
                output.flush(); kernel_receipts.append(receipt)
                print('KERNEL', index + 1, '/54', 'cases', receipt['cases'], flush=True)
        write_once(root / 'kernel-receipts.json', kernel_receipts)
        write_once(root / 'enabled-phases.json', phases)
        from .analysis import analyse
        output = analyse(root, protocol | {'analysis_phases': phases}, deadline)
        status(root, {'status': 'SEARCH_MECHANISM_COMPLETE', 'completed': 90 if gate['triggered'] else 54,
                      'analysis': str(output.relative_to(root)), 'wallSeconds': deadline.elapsed(),
                      'step6Allowed': False, 'additionalExperiments': False})
        print('SEARCH_MECHANISM_COMPLETE', output, flush=True)
    return root


if __name__ == '__main__':
    campaign(sys.argv[1])

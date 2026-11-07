"""Foreground Linux execution and non-overwriting receipts for the donor probe."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def one(path):
    lines = Path(path).read_text().splitlines()
    assert len(lines) == 1
    return json.loads(lines[0])


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def load():
    return {'epoch': time.time(), 'load': os.getloadavg(), 'memory': Path('/proc/meminfo').read_text(),
            'processes': subprocess.check_output(['ps', '-eo', 'pid,user,pcpu,pmem,comm', '--sort=-pcpu'], text=True).splitlines()[:14]}


def execute(command, out, *, expected_failure=False):
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'command.json', command); write(out / 'load-before.json', load())
    start = time.perf_counter()
    with (out / 'run.log').open('w') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    write(out / 'process.json', {'exitCode': result.returncode, 'seconds': time.perf_counter() - start})
    write(out / 'load-after.json', load())
    assert (result.returncode != 0) == expected_failure, str(out)


def input_paths(anchor, stem):
    root = anchor / 'payload/inputs' / stem
    return [root / (stem + '.txt'), root / 'RECONSTRUCTED-setup.txt', root / 'fatigue-input.txt']


def source_run(anchor, root, build, java, stem, seed):
    out = root / 'sources' / stem / str(seed)
    capture = root / 'capture' / stem / str(seed)
    options = [v for v in read(anchor / 'payload/anchor-vm-options.json') if not v.startswith('-Dresearch.pa.auditPaid=')]
    options += ['-Dresearch.pa.auditPaid=true', '-Dresearch.donor.capture=' + str(capture)]
    command = ['nice', '-n', '10', str(java), *options, '-cp', (build / 'classpath.txt').read_text().strip(),
               'research.dynamic.PilotRun', *map(str, input_paths(anchor, stem)), str(out), 'FULL', '500000', str(seed), 'Infinity']
    execute(command, out)
    receipt = one(out / 'run-receipt.jsonl')
    original = anchor / 'science' / stem / str(seed) / 'FULL'
    old = one(original / 'run-receipt.jsonl')
    assert receipt['successful'] == receipt['attempted'] == 500000 and receipt['failed'] == 0
    assert receipt['paidSHA256'] == old['paidSHA256'], 'Capture changed full paid trajectory'
    def fronts(path):
        return {r['checkpoint']: r['front'] for r in map(json.loads, path.read_text().splitlines()) if r['checkpointKind'] == 'FE' and r['reached']}
    assert fronts(out / 'anytime.jsonl') == fronts(original / 'anytime.jsonl')
    assert (out / 'initial-population.jsonl').read_bytes() == (original / 'initial-population.jsonl').read_bytes()
    snapshot = read(capture / 'capture.json')
    assert snapshot['passed'] and snapshot['beforeGlobalFE'] >= 250000 and snapshot['afterGlobalFE'] - snapshot['beforeGlobalFE'] == 5000
    rows = (capture / 'points.tsv').read_text().splitlines()
    assert len(rows) == 5100 and sum(line.startswith('P\t') for line in rows) == 100
    write(out / 'equivalence.json', {'passed': True, 'original': str(original), 'fullPaidSHA256': receipt['paidSHA256'],
                                    'newActualFE': 500000, 'capture': snapshot,
                                    'captureSHA256': hashlib.sha256((capture / 'points.tsv').read_bytes()).hexdigest()})
    print('CAPTURE_EQUIVALENT', stem, seed, snapshot['beforeGlobalFE'], snapshot['sharedPaidCandidates'], flush=True)


def probe_run(anchor, root, build, java, stem, seed, mode, *, label=None, engineering=False, limit=None, fail=False, import_qa=False):
    out = root / ('engineering' if engineering else 'science') / stem / str(seed) / (label or mode)
    options = ['-Dresearch.pilot.physics=' + str(engineering).lower(), '-Dresearch.donor.importQA=' + str(import_qa).lower()]
    if limit is not None: options.append('-Dresearch.donor.limit=' + str(limit))
    if fail: options.append('-Dresearch.pilot.failAt=2')
    command = ['nice', '-n', '10', str(java), *options, '-cp', (build / 'classpath.txt').read_text().strip(),
               'research.dynamic.DonorProbeRun', *map(str, input_paths(anchor, stem)), str(out),
               str(root / 'capture' / stem / str(seed)), mode, str(seed)]
    execute(command, out, expected_failure=fail)
    receipt = read(out / 'receipt.json')
    if fail:
        assert receipt['attempted'] == 2 and receipt['successful'] == 1 and receipt['failed'] == 1
    else:
        target = limit if limit is not None else receipt['expectedFE']
        assert receipt['attempted'] == receipt['successful'] == target and receipt['failed'] == 0
        assert receipt['decoder']['dynamic.evaluations'] == target
    if engineering: assert receipt['physicsQA']['fullTimelineChecks'] == receipt['successful']
    return out, receipt

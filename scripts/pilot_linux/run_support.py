"""Linux-only foreground JVM runs and retained receipts; no detached worker."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import time


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text('utf-8-sig').splitlines() if line]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def host_snapshot():
    return {'time': time.time(), 'host': platform.node(), 'load': os.getloadavg(),
            'memory': Path('/proc/meminfo').read_text(),
            'processes': subprocess.run(['ps', '-eo', 'pid,user,pcpu,pmem,comm', '--sort=-pcpu'],
                                       capture_output=True, text=True, check=True).stdout.splitlines()[:16]}


def initial(path):
    return [{k: value for k, value in r.items() if k in ('JS', 'FA', 'MA', 'WA', 'objectives', 'fe')}
            for r in rows(path / 'initial-population.jsonl')]


def front_map(path):
    return {int(r['checkpoint']): sorted(map(tuple, r['front'])) for r in rows(path / 'anytime.jsonl')
            if r['checkpointKind'] == 'FE' and r['reached']}


def run_case(payload, build, java, out, instance, seed, phase, limit, *, baseline=False,
             observation=True, physics=False, failure=-1, seconds=None):
    if platform.system() != 'Linux':
        raise RuntimeError('Search is restricted to Linux')
    out.mkdir(parents=True, exist_ok=False)
    cp = (build / ('base-classpath.txt' if baseline else 'classpath.txt')).read_text().strip()
    options = [v for v in read(payload / 'anchor-vm-options.json') if not v.startswith('-Dresearch.pa.auditPaid=')]
    options += ['-Dresearch.pa.auditPaid=true', '-Dresearch.pilot.observationOff=' + str(not observation).lower(),
                '-Dresearch.pilot.physics=' + str(physics).lower(), '-Dresearch.pilot.failAt=' + str(failure)]
    inputs = payload / 'inputs' / instance
    command = ['nice', '-n', '10', str(java), *options, '-cp', cp,
               'research.dynamic.GomCapabilityRun' if baseline else 'research.dynamic.PilotRun',
               str(inputs / (instance + '.txt')), str(inputs / 'RECONSTRUCTED-setup.txt'),
               str(inputs / 'fatigue-input.txt'), str(out), 'SHARE_CTX_GOM' if baseline else phase,
               str(limit), str(seed), 'Infinity' if seconds is None else str(seconds)]
    write(out / 'command.json', command)
    write(out / 'external-load-before.json', host_snapshot())
    start = time.perf_counter()
    with (out / 'run.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
    write(out / 'process.json', {'exitCode': result.returncode, 'processSeconds': time.perf_counter()-start})
    write(out / 'external-load-after.json', host_snapshot())
    receipt_path = out / 'run-receipt.jsonl'
    if not receipt_path.exists():
        raise RuntimeError('No receipt: ' + str(out))
    receipt = rows(receipt_path)[0]
    if failure > 0:
        assert result.returncode != 0 and receipt['attempted'] == failure and receipt['failed'] == 1
        assert receipt['successful'] == failure-1 and (out / 'failure-last-front.jsonl').exists()
    else:
        assert result.returncode == 0 and receipt['error'] is None, str(out)
        if seconds is None:
            assert receipt['attempted'] == receipt['successful'] == limit and receipt['failed'] == 0, str(out)
        if seconds is None:
            assert receipt['decoder']['dynamic.evaluations'] == receipt['successful']
        else:
            assert receipt['stopReason'] == 'TIME_LIMIT'
            assert receipt['successful'] <= receipt['decoder']['dynamic.evaluations'] <= receipt['attempted']
            assert receipt['attempted'] == receipt['successful'] + receipt['failed']
        assert read(out / 'checkpoint-validation.json')['status'] == 'passed'
    print('DONE', instance, seed, phase, limit, receipt['stopReason'], round(receipt['searchSeconds'], 3), flush=True)
    return receipt


def verify_artifacts(payload):
    for name, item in read(payload / 'transfer-manifest.json').items():
        assert sha(payload / name) == item['sha256'], name


def accounting(root):
    values = [rows(p)[0] for p in root.rglob('run-receipt.jsonl')]
    return {name: sum(r[name] for r in values) for name in ('attempted', 'successful', 'failed')}

"""Reuse the exact accepted evaluator; enforce this study's stricter 60+4 cap."""
import argparse
from importlib.metadata import version
from pathlib import Path
import subprocess
import sys
import time
from transfer_common import *
from verify_transfer import preflight, audit_phase


def invoke(root, kind, count):
    out = root / kind
    out.mkdir()
    data = ANCHOR / 'payload/inputs' / STEM
    command = ['nice', '-n', '10', str(BASE / 'runtime/jdk17/bin/java'), '-Xms128m', '-Xmx2g',
        '-cp', (CF / 'build-01/classpath.txt').read_text().strip(), 'research.dynamic.CounterfactualRun',
        str(data / (STEM + '.txt')), str(data / 'RECONSTRUCTED-setup.txt'),
        str(data / 'fatigue-input.txt'), str(root / (kind + '.tsv')), str(out), kind.upper(), str(count)]
    write(out / 'command.json', command)
    start = time.perf_counter()
    with (out / 'run.log').open('x') as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    write(out / 'process.json', dict(exitCode=process.returncode, seconds=time.perf_counter()-start))
    assert process.returncode == 0, 'Failure retained; do not refill budget or replace a receiver'
    receipt = read(out / 'receipt.json')
    if kind == 'qa':
        assert (receipt['attemptedQA'], receipt['passedQA'], receipt['failedQA']) == (count, count, 0)
        assert receipt['maxAbsoluteObjectiveError'] == [0, 0, 0]
    else:
        assert (receipt['attempted'], receipt['successful'], receipt['failed'], receipt['written']) == (count, count, 0, count)
        assert receipt['decoder']['dynamic.evaluations'] == count
        assert receipt['decoder']['dynamic.reusedOperations'] == 0
    assert receipt['pending'] is None and receipt['error'] is None
    print('DONE', kind, count, audit_phase(root, kind), flush=True)


def main(root):
    prepare()
    protocol = read(root / 'protocol.json')
    assert (protocol['plannedNewEvaluations'], protocol['plannedQA']) == (60, 4)
    assert not (root / 'qa').exists() and not (root / 'paid').exists()
    assert read(CF / 'paid-independent-audit.json')['passed']
    write(root / 'preflight.json', preflight(root))
    write(root / 'execution-identity.json', dict(
        inheritedClassIdentity=read(CF / 'build-01/identity.json'),
        classpath=(CF / 'build-01/classpath.txt').read_text(),
        source={p.name: sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))},
        python=sys.version, platform=sys.platform,
        packages={name: version(name) for name in ('numpy', 'moocore')},
        java=subprocess.check_output([str(BASE / 'runtime/jdk17/bin/java'), '-version'],
                                     stderr=subprocess.STDOUT, text=True)))
    invoke(root, 'qa', 4)
    assert read(root / 'qa-audit.json')['passed']
    write(root / 'qa-gate.json', dict(passed=True, exactOldObjectiveBits=True,
                                    qa=4, paidQueriesBeforeGate=0))
    invoke(root, 'paid', 60)
    write(root / 'completion.json', dict(passed=True, paidAttempted=60, paidSuccessful=60,
                                       failed=0, qaAttempted=4, qaSuccessful=4, unchangedMainline=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)

"""One read-only PA source prefix; gate all subsequent work on paid-prefix identity."""
import argparse
import csv
import itertools
from common import *


def build(root):
    output = root/'build'
    output.mkdir()
    classes = output/'classes'
    classes.mkdir()
    cp = (OLD/'build-01/classpath.txt').read_text().strip()
    sources = sorted((root/'source/java').glob('*.java'))
    command = [str(BASE/'runtime/jdk17/bin/javac'), '-encoding', 'UTF-8', '--release', '8',
               '-implicit:none', '-cp', cp, '-d', str(classes), *map(str, sources)]
    execute(command, output/'compile')
    dependencies = {}
    for entry in cp.split(':'):
        p = Path(entry)
        dependencies[entry] = ({str(f.relative_to(p)): sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
                               if p.is_dir() else sha(p))
    write(output/'identity.json', dict(sources={p.name: sha(p) for p in sources}, dependencies=dependencies,
          classes={str(p.relative_to(classes)): sha(p) for p in classes.rglob('*.class')},
          java=subprocess.check_output([str(JAVA), '-version'], stderr=subprocess.STDOUT, text=True),
          python=sys.version, protocolSHA256=sha(root/'protocol.md')))
    (output/'classpath.txt').write_text(str(classes)+':'+cp)


def capture(root):
    old = OLD/'capture/PA_JOINT'
    command = read(old/'command.json')
    java_index = command.index(str(JAVA))
    options = command[java_index+1:command.index('-cp')]
    options.append('-Dresearch.midSupport.models='+str(root/'pa-source/models.jsonl'))
    cmd = ['nice', '-n', '10', str(JAVA), *options, '-cp', (root/'build/classpath.txt').read_text(),
           'research.dynamic.GomCapabilityRun', *input_args(), str(root/'pa-source'), 'PA_JOINT',
           '250000', str(SEED), 'Infinity']
    execute(cmd, root/'pa-source')
    receipt, = rows(root/'pa-source/run-receipt.jsonl')
    trace, = rows(root/'pa-source/trajectory-receipt.jsonl')
    assert receipt['attempted'] == receipt['successful'] == trace['paidRows'] == 250000
    assert receipt['failed'] == 0 and receipt['error'] is None
    with (old/'trajectory-paid.csv').open() as a, (root/'pa-source/trajectory-paid.csv').open() as b:
        first, second = csv.DictReader(a), csv.DictReader(b)
        count = 0
        for expected, observed in itertools.zip_longest(itertools.islice(first, 250000), second):
            assert expected == observed, ('Paid-prefix divergence', count+1)
            count += 1
    assert count == 250000 and gap.initial(old) == gap.initial(root/'pa-source')
    old_cp, new_cp = gap.checkpoints(old), gap.checkpoints(root/'pa-source')
    common = sorted(set(old_cp) & set(new_cp))
    assert common and all(old_cp[k] == new_cp[k] for k in common)
    qa = read(root/'pa-source/checkpoint-validation.json')
    assert qa['status'] == 'passed' and qa['allReachedPointsCovered'] and qa['uniqueOfflineDecodes'] <= 10000
    old_identity, = rows(old/'loaded-identity.jsonl')
    identity, = rows(root/'pa-source/loaded-identity.jsonl')
    for name, info in old_identity.items():
        if isinstance(info, dict) and 'sha256' in info:
            assert identity[name]['sha256'] == info['sha256'], name
    write(root/'source-gate.json', dict(passed=True, actualFE=250000, failed=0, paidCSVRowsEqual=count,
          initialEqual=True, publicCheckpointsEqual=common, loadedCoreClassesEqual=True,
          extraQA=qa['uniqueOfflineDecodes'], observationNanos=trace['observationNanos'],
          paidSHA256=trace['paidSHA256'], modelSnapshots=len(rows(root/'pa-source/models.jsonl'))))
    print('SOURCE_GATE_PASSED', count, flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root', type=Path);args=p.parse_args();linux()
    build(args.root);capture(args.root)

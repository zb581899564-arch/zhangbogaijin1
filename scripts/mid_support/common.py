"""Frozen identities and IO for the middle-budget resource-only counterfactual."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import time

BASE = Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
OLD = BASE / 'runs/linux-trajectory-gap-20261107-01'
ANCHOR = BASE / 'runs/linux-pilot-evaluation-20261106-01/payload'
JAVA = BASE / 'runtime/jdk17/bin/java'
STEM = '100_2_3_1'
SEED = 14910003
ARMS = ('S_RESOURCE', 'PA_RESOURCE', 'PA_SHUFFLED')
ROLES = ('MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST')
FIELDS = ('JS', 'FA', 'MA', 'WA')
spec = importlib.util.spec_from_file_location('gap_common', OLD / 'update-01/scripts/common.py')
gap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gap)
read, rows, write, sha = gap.read, gap.rows, gap.write, gap.sha
nd, metrics, coverage, csv_write = gap.nondominated, gap.metrics, gap.coverage, gap.csv_write
SCALE = gap.SCALES[STEM]


def linux():
    assert sys.platform == 'linux' and sys.version_info[:2] == (3, 11)


def stream(path):
    with Path(path).open(encoding='utf-8-sig') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def jsonl(path, values):
    with Path(path).open('x', encoding='utf-8') as f:
        for value in values:
            f.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')


def execute(command, folder):
    folder.mkdir(parents=True, exist_ok=False)
    write(folder / 'command.json', command)
    start = time.monotonic()
    before = os.getloadavg()
    with (folder / 'run.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'})
    write(folder / 'process.json', dict(exitCode=result.returncode, seconds=time.monotonic()-start,
          loadBefore=before, loadAfter=os.getloadavg()))
    assert result.returncode == 0, 'Failure retained, no automatic retry: ' + str(folder)


def java(root, entry):
    return ['nice', '-n', '10', str(JAVA), '-Xms128m', '-Xmx2g', '-cp',
            (root/'build/classpath.txt').read_text().strip(), entry]


def input_args():
    folder = ANCHOR/'inputs'/STEM
    return [str(folder/(STEM+'.txt')), str(folder/'RECONSTRUCTED-setup.txt'), str(folder/'fatigue-input.txt')]


def encode(resources, keys, catalog):
    js = sorted(range(len(keys)), key=lambda j: (keys[j], -j))
    return dict(JS=js, **{name: [catalog[resources[j]][k] for j in js]
                         for k, name in enumerate(('FA', 'MA', 'WA'))})


def physical(row):
    return (tuple(row['resources']), tuple(tuple(j for j, f in zip(row['JS'], row['FA']) if f == i)
                                         for i in range(max(row['FA'])+1)))


def csv_value(values):
    return ','.join(map(str, values))


def tsv_row(row, qa=False):
    # mask=1 is only the legacy evaluator transport tag; actual FOS is in queries.jsonl.
    return '\t'.join([row['id'], '0' if qa else '1', csv_value(row['resources']), csv_value(row['keys']),
                      *(csv_value(row[f]) for f in FIELDS), csv_value(row['objectives']) if qa else ''])

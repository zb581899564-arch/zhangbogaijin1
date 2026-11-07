"""Read-only source/genome parsing and strict evidence checks."""
from functools import lru_cache
import json
import math
from pathlib import Path
import numpy as np
from common import SEEDS, read, sha

RAW = ('JS', 'FA', 'MA', 'WA', 'objectives')
FACTORY = ('factoryMakespan', 'factoryEnergy', 'factoryCost')
ROLE = {'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}
ARMS = ('ROLE', 'REQUEST', 'ORDINARY', 'SHUFFLED')
RECORD = ('jobs', 'machines', 'workers', 'objectives', 'paidFE', 'stage')
PROPOSAL = ('receiver', 'slot', 'role', 'round', 'step', 'subset', 'donorSlot', 'mask',
            'parentId', 'donorId', 'parentPaidFE', 'donorPaidFE',
            'parentSourcePaidByFE', 'donorSourcePaidByFE')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def lines(path):
    with path.open(encoding='utf-8-sig') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def same(actual, expected, message):
    require(actual == expected, message + ': ' + repr(actual)[:180] + ' != ' + repr(expected)[:180])


def raw(row):
    return {key: row[key] for key in RAW}


def csv_values(value, cast=int):
    return [cast(v) for v in value.split(',')] if value else []


def raw_fields(fields):
    return dict(objectives=csv_values(fields[0], float),
                **{key: csv_values(value) for key, value in zip(RAW[:4], fields[1:])})


def request_file(path):
    rows = path.read_text(encoding='utf-8-sig').splitlines()
    require(len(rows) == 1, 'One request required: ' + str(path))
    values = rows[0].split('\t')
    require(len(values) == 11, 'Request column count differs')
    spec = dict(requestId=values[0], family=int(values[1]))
    spec.update(zip(('cap', 'eta', 'energyScale', 'wageScale'), map(float, values[2:6])))
    return spec, raw_fields(values[6:])


def fixed(row):
    require(sorted(row['JS']) == list(range(len(row['JS']))), 'JS is not a complete permutation')
    return dict(zip(row['JS'], row['FA']))


def check_raw(row, context):
    count = len(context['fixed'])
    require(all(len(row[key]) == count for key in RAW[:4]), 'Genome length differs')
    same(fixed(row), context['fixed'], 'Fixed-FA job assignment changed')
    require(all(type(v) is int and v >= 0 for key in RAW[:4] for v in row[key]), 'Invalid resource index')
    require(len(row['objectives']) == 3 and all(math.isfinite(v) for v in row['objectives']), 'Invalid objectives')


def check_factory(row, factories):
    for key in FACTORY:
        require(len(row[key]) == factories and all(math.isfinite(v) and v >= 0 for v in row[key]),
                'Missing or invalid independently required factory data: ' + key)
    combined = [max(row[FACTORY[0]]), sum(row[FACTORY[1]]), sum(row[FACTORY[2]])]
    require(np.allclose(row['objectives'], combined, rtol=1e-12, atol=1e-10),
            'Whole objectives disagree with factory decomposition')


@lru_cache(maxsize=None)
def capture_requests(root, stem, seed):
    return {r['requestOrdinal']: r for r in lines(Path(root)/'capture'/stem/seed/'requests.jsonl')
            if r['type'] == 'compose-request'}


def load_context(root, directory, stem, seed, q):
    folder = root/directory/stem/seed/q
    actual, parent = request_file(folder/'request.tsv')
    effective, effective_parent = request_file(folder/'effective-request.tsv')
    provenance = read(folder/'provenance.json')
    captured = capture_requests(str(root), stem, seed)[int(actual['requestId'])]
    capture = root/'capture'/stem/seed
    same(provenance['requestSourceSHA256'], sha(capture/'requests.jsonl'), 'Source request evidence changed')
    same(provenance['targetRequest'], int(actual['requestId']), 'Target request provenance differs')
    same(provenance['shuffledRequest'], int(effective['requestId']), 'Shuffled request provenance differs')
    same(actual['family'], SEEDS.index(int(seed)) % 4, 'Predeclared source family changed')
    siblings = sorted(p for p in folder.parent.iterdir() if p.is_dir() and p.name.isdigit())
    following, following_parent = request_file(folder.parent/str((int(q)+1) % len(siblings))/'request.tsv')
    same((effective, effective_parent), (following, following_parent), 'Shuffled request is not the fixed cyclic-next source request')
    same(raw(captured['parent']), parent, 'Actual request parent changed from captured evidence')
    for key in ('family', 'cap', 'eta', 'energyScale', 'wageScale'):
        same(actual[key], captured[key], 'Actual request parameter differs: ' + key)
    points = []
    for index, line in enumerate((folder/'points.tsv').read_text().splitlines()):
        v = line.split('\t')
        require(len(v) == 10 and v[0] == 'P' and int(v[1]) == index, 'Malformed P100 input order')
        points.append(dict(raw_fields(v[5:]), role=v[3], family=int(v[4]), sourcePaidByFE=int(v[2])))
    require(len(points) == 100, 'Expected original mature P100')
    same((folder/'points.tsv').read_text().splitlines(), (capture/'points.tsv').read_text().splitlines()[:100],
         'Imported P100 differs from captured mature receivers')
    same(read(folder/'background.json'), read(capture/'background.json'), 'Common A0 differs from source post-global archive')
    factories = int(stem.split('_')[2])
    pools = [[] for _ in range(factories)]
    for line in (folder/'pools.tsv').read_text().splitlines():
        v = line.split('\t'); require(len(v) == 6, 'Retained pool column count differs')
        require(int(v[1]) >= -1, 'Invalid historical paidFE; -1 must remain untracked')
        pools[int(v[0])].append(dict(objectives=csv_values(v[2], float), jobs=csv_values(v[3]),
            machines=csv_values(v[4]), workers=csv_values(v[5]), paidFE=int(v[1]), stage='IMPORTED_RETAINED'))
    for f, pool in enumerate(pools):
        expected = [{key: r[key] for key in RECORD if key != 'stage'} for r in captured['pools'][f]['records']]
        same([{key: r[key] for key in RECORD if key != 'stage'} for r in pool], expected,
             'Input retained records/order differ from actual capture')
    return dict(folder=folder, actual=actual, shuffled=effective, parent=parent, fixed=fixed(parent),
                factories=factories, pools=pools, points=points, background=read(folder/'background.json'),
                captured=captured, provenance=provenance)

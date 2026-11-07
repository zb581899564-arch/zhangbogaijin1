"""Independent saved-evidence audit; no new model calls or search evaluations."""
from pathlib import Path
from collections import Counter
import argparse
import csv
import math
import platform
import sys
import time
import numpy as np

for project in Path(__file__).resolve().parents:
    if (project/'research/pilot_evaluation').is_dir():
        sys.path.insert(0, str(project))
        break

from research.dynamic_benchmark.metrics import hypervolume
from research.expansion_audit.metrics import grid_hv

from run_support import read, rows, write, initial, front_map


def weak(a, b):
    return all(x <= y for x, y in zip(a, b))


def offer(front, value):
    if any(weak(p, value) for p in front):
        return front
    return [p for p in front if not weak(value, p)] + [value]


def audit_run(out, class_identity, scale):
    receipt = rows(out/'run-receipt.jsonl')[0]
    assert receipt['successful'] == receipt['attempted'] == 500000 and receipt['failed'] == 0
    assert receipt['stopReason'] == 'FE_LIMIT' and receipt['decoder']['dynamic.evaluations'] == 500000
    loaded = rows(out/'loaded-identity.jsonl')[0]
    for name, expected in class_identity.items():
        assert loaded[name]['sha256'] == expected, (out, name)
    snapshots = front_map(out)
    assert {1, 2, 100, 10000, 50000, 100000, 250000, 500000} <= set(snapshots)
    for front in snapshots.values():
        normalized = np.asarray(front)/scale
        for ref in (1.25,1.5,2.0):
            assert math.isclose(hypervolume(normalized,[ref]*3), grid_hv(normalized,ref), rel_tol=1e-11, abs_tol=1e-12)
    front, count, last_time = [], 0, -1
    stages, sources, admission_fees = Counter(), Counter(), set()
    with (out/'paid-events.csv').open() as f:
        for r in csv.DictReader(f):
            count += 1
            assert int(r['fe']) == count
            seconds = float(r['elapsedSeconds'])
            assert math.isfinite(seconds) and seconds >= last_time
            last_time = seconds
            value = tuple(float(r[k]) for k in ('Cmax','TEC','TWC'))
            assert all(math.isfinite(x) for x in value)
            stages[r['stage']] += 1
            sources[r['stage']+'/'+r['source']] += 1
            if int(r['admitted']):
                admission_fees.add(count)
                front = offer(front, value)
            if count in snapshots:
                assert sorted(front) == snapshots[count], (out, count, 'chronological front')
    assert count == 500000
    expected = receipt['trace']['phaseFE']
    assert {**dict(stages), **dict(sources)} == expected
    stage_admissions = {r['fe'] for r in rows(out/'stage-events.jsonl') if r['kind'] == 'admission'}
    assert admission_fees == stage_admissions
    for r in rows(out/'checkpoint-solutions.jsonl'):
        if r['checkpointKind'] != 'FE':
            continue
        assert 1 <= r['bornFE'] <= r['checkpoint'] == r['checkpointFE']
        assert r['bornSeconds'] <= r['checkpointElapsedSeconds']
        assert tuple(r['objectives']) in snapshots[int(r['checkpoint'])]
        assert r['bornFE'] in admission_fees
    assert math.isclose(sum(receipt['trace']['phaseSecondsInclusive'].values()), receipt['searchSeconds'], abs_tol=1e-8)
    return {'paidRows': count, 'admissions': len(admission_fees), 'fronts': len(snapshots),
            'stageFees': dict(stages), 'checkpointOfflineDecodes': read(out/'checkpoint-validation.json')['uniqueOfflineDecodes']}


def audit(root, output):
    if platform.system() != 'Linux':
        raise RuntimeError('Linux-only statistics')
    start = time.perf_counter()
    assert read(root/'science-complete.json')['passed']
    plan = read(root/'protocol.json')
    loaded = rows(root/'engineering/20_8_5_1/FULL/loaded-identity.jsonl')[0]
    identity = {k: v['sha256'] for k, v in loaded.items() if isinstance(v, dict) and 'sha256' in v}
    result = {}
    for spec in plan['instances']:
        for seed in plan['seeds']:
            common = None
            for arm in plan['arms']:
                out = root/'science'/spec['stem']/str(seed)/arm
                value = initial(out)
                assert len(value) == 100 and all(set(r) == {'JS','FA','MA','WA','objectives','fe'} for r in value)
                if common is None:
                    common = value
                assert value == common
                key = str(out.relative_to(root))
                result[key] = audit_run(out, identity, spec['normalization']['scale'])
                print('AUDIT_OK', key, flush=True)
    assert len(result) == 18 and sum(r['paidRows'] for r in result.values()) == 9000000
    write(output, {'passed': True, 'runs': result, 'scienceFE': 9000000,
                   'newSearchFE': 0, 'newDecoderCalls': 0, 'offlineSeconds': time.perf_counter()-start,
                   'independentHVChecks': sum(r['fronts'] for r in result.values())*3,
                   'method': 'Independent tuple dominance replay of every logged admission; all paid row fees/times/sources, checkpoint birth and full vectors, loaded classes and paired initial genomes verified',
                   'limit': 'Does not recompute every rejected candidate admission; common archive mathematics and checkpoint full decoding separately checked'})


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.root.resolve(), args.output.resolve())

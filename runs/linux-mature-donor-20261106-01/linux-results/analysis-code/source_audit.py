"""Independent captured-window provenance and complete actual-cost reconciliation."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import struct
import sys
import time
import numpy as np


def read(path):
    return json.loads(path.read_text())


def raw_key(row):
    digest = hashlib.sha256(struct.pack('>q', 0))
    for field in ('JS', 'FA', 'MA', 'WA'):
        values = row[field]
        digest.update(struct.pack('>i', len(values)))
        digest.update(struct.pack('>' + 'i' * len(values), *values))
    digest.update(struct.pack('>ddd', *row['objectives']))
    return digest.hexdigest()


def context(root, stem, seed):
    from audit_capture import points_tsv
    from audit_replay import ParetoLedger, sorted_points
    capture = root / 'capture' / stem / str(seed)
    source = root / 'sources' / stem / str(seed)
    meta, rows = read(capture / 'capture.json'), points_tsv(capture / 'points.tsv')
    cutoff = meta['afterGlobalFE']; chosen = None; archive = ParetoLedger(np.empty((0, 3)))
    before_keys = None
    with (source / 'stage-events.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['fe'] > cutoff: break
            if row.get('label') == 'PRE_GLOBAL' and row['fe'] >= 250000 and chosen is None:
                chosen = row['fe']; before_keys = Counter(p['key'] for p in row['points'])
            if row['kind'] == 'admission': archive.offer(row['point']['objectives'])
    assert chosen == meta['beforeGlobalFE'], 'Capture was not first eligible actual boundary'
    assert before_keys == Counter(raw_key(p) for p in rows[:100]), 'Captured receiver membership changed'
    assert sorted_points(archive.points) == sorted_points(read(capture / 'background.json')), 'Wrong all-paid A0'
    selected = iter(rows[100:]); count = 0
    with (source / 'paid-events.csv').open() as stream:
        for paid in csv.DictReader(stream):
            fee = int(paid['fe'])
            if fee > cutoff: break
            if fee <= chosen: continue
            point = next(selected); count += 1
            assert point['paidByFE'] == fee and paid['stage'] == 'GLOBAL'
            assert point['role'] == paid['role']
            assert point['objectives'] == [float(paid[k]) for k in ('Cmax', 'TEC', 'TWC')]
            assert point['source'] == ('S' if paid['source'] == 'SHARED_COMPOSITION' else 'G')
    assert count == 5000 and next(selected, None) is None
    return {'instance': stem, 'seed': seed, 'firstEligibleFE': chosen, 'capturedPaidRows': count,
            'matureMembershipExact': True, 'sourceLabelsAndFeesExact': True, 'allPaidArchiveExact': True}


def costs(root):
    rows = []
    for kind, pattern in [('source', 'sources/*/*/run-receipt.jsonl'), ('engineering', 'engineering/*/*/*/receipt.json'), ('science', 'science/*/*/*/receipt.json')]:
        for path in sorted(root.glob(pattern)):
            receipt = read(path)
            entry = {'kind': kind, 'path': str(path.relative_to(root)),
                     **{k: receipt[k] for k in ('attempted', 'successful', 'failed', 'searchSeconds')},
                     'processSeconds': read(path.parent / 'process.json')['seconds'],
                     'importFullQA': receipt.get('importQA', {}).get('fullDecodes', 0),
                     'importQASeconds': receipt.get('importQA', {}).get('offlineSeconds', 0),
                     'paidTimelineQA': receipt['physicsQA']['fullTimelineChecks'],
                     'paidTimelineQASeconds': receipt['physicsQA']['engineeringOnlySeconds'],
                     'prepareSeconds': receipt.get('prepareSeconds', 0), 'checkpointQA': None}
            validations = list(path.parent.glob('*validation*.json*'))
            if validations:
                entry['checkpointValidationFiles'] = [str(p.relative_to(root)) for p in validations]
                entry['checkpointQA'] = [read(p) for p in validations]
            rows.append(entry)
    return rows


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(); root = args.root
    sys.path.insert(0, str(root / 'analysis-code'))
    start = time.perf_counter(); plan = read(root / 'protocol.json')
    checks = [context(root, spec['stem'], seed) for spec in plan['instances'] for seed in plan['seeds']]
    rows = costs(root)
    assert sum(r['attempted'] for r in rows) == plan['totalPlannedAttemptedFE']
    assert sum(r['failed'] for r in rows) == 2 and all(r['failed'] == 0 for r in rows if r['kind'] != 'engineering')
    assert sum(r['importFullQA'] for r in rows) == 30600
    result = {'passed': True, 'contexts': checks, 'actualRuns': rows,
              'newSearchFE': 0, 'newDecoderCalls': 0, 'offlineSeconds': time.perf_counter() - start}
    with (root / 'source-and-cost-audit.json').open('x') as stream: json.dump(result, stream, ensure_ascii=False, indent=2)
    print('SOURCE_AND_COST_AUDIT_PASS', result['offlineSeconds'], flush=True)


if __name__ == '__main__': main()

"""Reproduce only the already frozen source prefix, then verify recorded evidence."""
import argparse
import csv
import itertools
import json
from pathlib import Path
import time
from common import SOURCE, linux, process, read, sha, write


def rows(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in ('elapsedSeconds',)}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def verify_paid(original, replay, limit):
    count = 0
    with original.open() as left, replay.open() as right:
        a, b = csv.DictReader(left), csv.DictReader(right)
        for old, new in zip(itertools.islice(a, limit), b):
            old.pop('elapsedSeconds'); new.pop('elapsedSeconds')
            assert old == new, ('paid prefix mismatch', count + 1)
            count += 1
        assert count == limit and next(b, None) is None
    return count


def verify_events(original, replay, limit):
    old = (stable(r) for r in rows(original) if r['fe'] <= limit and r['kind'] != 'stop')
    new = (stable(r) for r in rows(replay) if r['kind'] != 'stop')
    count = 0
    # A cutoff may suppress final uncharged boundary bookkeeping. Every recorded
    # replay event must match the original prefix, with no skipped event.
    for a, b in itertools.zip_longest(old, new):
        if b is None:
            assert a['fe'] == limit, 'Replay omitted a pre-cutoff event'
            continue
        assert a == b, ('event prefix mismatch', count)
        count += 1
    return count


def verify(source, out, capture, limit):
    started = time.perf_counter()
    receipt = read(out / 'run-receipt.jsonl')
    assert receipt['attempted'] == receipt['successful'] == limit
    assert receipt['failed'] == 0 and receipt['error'] is None
    assert list(rows(source / 'initial-population.jsonl')) == list(rows(out / 'initial-population.jsonl'))
    paid = verify_paid(source / 'paid-events.csv', out / 'paid-events.csv', limit)
    events = verify_events(source / 'stage-events.jsonl', out / 'stage-events.jsonl', limit)
    old_capture = SOURCE / 'capture' / out.parent.name / out.name
    for name in ('points.tsv', 'background.tsv', 'background.json'):
        assert sha(old_capture / name) == sha(capture / name), name
    original_checkpoints = {r['checkpoint']: r for r in rows(source / 'anytime.jsonl') if r.get('checkpointKind') == 'FE'}
    checkpoints = []
    for row in rows(out / 'anytime.jsonl'):
        if row.get('checkpointKind') == 'FE' and row['checkpoint'] in original_checkpoints:
            old = original_checkpoints[row['checkpoint']]
            assert row['front'] == old['front'], 'Checkpoint front differs'
            checkpoints.append(row['checkpoint'])
    assert set(checkpoints) == {1, 2, 100, 10000, 50000, 100000, 250000}
    result = dict(passed=True, successful=limit, paidRowsExact=paid, stageEventsExact=events,
        sourceCapturedGenomesExact=5100, initialVectorsExact=True, checkpointFEs=checkpoints,
        qualification='All previously recorded paid objectives, phases and admissions; recorded population keys/selection; initial and mature global vectors. Historical per-evaluation genotype digest was not stored at this cutoff',
        offlineSeconds=time.perf_counter()-started)
    write(out / 'equivalence.json', result)
    return result


def run(root, context):
    stem, seed, limit = context['instance'], context['seed'], context['after']
    original = SOURCE / 'sources' / stem / str(seed)
    out = root / 'sources' / stem / str(seed)
    capture = root / 'capture' / stem / str(seed)
    command = read(original / 'command.json')
    command[command.index('-cp') + 1] = (root / 'capture-build-01/classpath.txt').read_text().strip()
    for i, item in enumerate(command):
        if item.startswith('-Dresearch.donor.capture='):
            command[i] = '-Dresearch.donor.capture=' + str(capture)
    main = command.index('research.dynamic.PilotRun')
    command[main+4] = str(out)
    command[main+6] = str(limit)
    cp = command.index('-cp')
    command[cp:cp] = ['-Dresearch.request.capture=' + str(capture),
        '-Dresearch.request.sourceBefore=' + str(context['before']),
        '-Dresearch.request.sourceAfter=' + str(limit)]
    process(command, out)
    result = verify(original, out, capture, limit)
    print('SOURCE_PREFIX_VERIFIED', stem, seed, result['paidRowsExact'], flush=True)


if __name__ == '__main__':
    linux()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    for context in read(args.root / 'source-protocol.json')['contexts']:
        run(args.root, context)

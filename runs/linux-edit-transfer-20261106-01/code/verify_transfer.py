"""Independent finite-proposal and paid-timeline audits; no decoder calls."""
from collections import Counter
import numpy as np
from transfer_common import *


def frozen_inputs(root):
    identities = read(root / 'input-identity.json')
    for path, digest in identities.items():
        assert sha(path) == digest, path
    return len(identities)


def proposal(query, source, receiver):
    assert fa_map(query) == fa_map(receiver) == fa_map(source['parent'])
    mask = query['sourceAtomMask']
    a, b = source['jobs']
    changed_resources, changed_keys = [], []
    for job, (resource, key) in enumerate(zip(query['resources'], query['keys'])):
        assert source['catalog'][resource]['factory'] == fa_map(receiver)[job]
        bit = 1 if job == a else 2 if job == b else 0
        allowed_resource = bool(bit and mask & bit)
        allowed_key = bool(bit and mask & (bit << 2))
        if query['arm'] in ('FULL', 'PRUNED'):
            expected_resource = source['child']['resources'][job] if allowed_resource else receiver['resources'][job]
            expected_key = source['child']['keys'][job] if allowed_key else receiver['keys'][job]
            assert resource == expected_resource and key == expected_key
        else:
            if not allowed_resource:
                assert resource == receiver['resources'][job]
            if not allowed_key:
                assert key == receiver['keys'][job]
        if resource != receiver['resources'][job]:
            changed_resources.append(job)
        if key != receiver['keys'][job]:
            changed_keys.append(job)
    assert query['changedFields'] == dict(resources=changed_resources, keys=changed_keys)
    for field, actual in encode(query['resources'], query['keys'], source['catalog']).items():
        assert query[field] == actual


def preflight(root):
    sources = {s['id']: s for s in read(root / 'sources.json')}
    receivers = {r['id']: r for r in read(root / 'receivers.json')}
    queries = read(root / 'queries.json')
    assert len(queries) == 60 and len(receivers) == 4
    assert len({q['id'] for q in queries}) == 60
    assert Counter(q['arm'] for q in queries) == {arm: 12 for arm in ARMS}
    blocks = {}
    for q in queries:
        proposal(q, sources[q['source']], receivers[q['receiver']])
        blocks.setdefault((q['source'], q['receiver']), {})[q['arm']] = q
    for block in blocks.values():
        for i in range(3):
            assert block[f'RANDOM_{i}']['changedFields'] == block['PRUNED']['changedFields']
    for r in receivers.values():
        assert np.any(np.all(np.asarray(next(iter(sources.values()))['A0']) <= r['objectives'], axis=1))
    return dict(passed=True, legalQueries=60, receivers=4, sourceIdentityChecks=frozen_inputs(root),
                actualChangedFieldMatchedControls=36, newDecoderCalls=0,
                neutralByArm=dict(Counter(q['arm'] for q in queries if q['neutralPhysical'])))


def audit_phase(root, kind):
    from audit import loaded_identity, timeline
    receipt = read(root / kind / 'receipt.json')
    class_checks = loaded_identity(CF, receipt)
    metadata = read(root / ('receivers.json' if kind == 'qa' else 'queries.json'))
    expected = {q['id']: q for q in metadata}
    rows = lines(root / kind / 'evaluations.jsonl')
    assert len(rows) == len(expected)
    operations, max_error = 0, 0.0
    for number, row in enumerate(rows, 1):
        assert row['number'] == number
        q = expected.pop(row['id'])
        assert row['mask'] == (0 if kind == 'qa' else 1)
        for field in (*FIELDS, 'resources', 'keys'):
            assert row[field] == q[field], (row['id'], field)
        if kind == 'qa':
            assert row['objectives'] == q['objectives']
        n, error = timeline(row)
        operations += n
        max_error = max(max_error, error)
    assert not expected
    report = dict(passed=True, rows=len(rows), operationRecords=operations,
                  classChecks=class_checks, sourceIdentityChecks=frozen_inputs(root),
                  maxIndependentAggregationError=max_error, newDecoderCalls=0)
    write(root / (kind + '-audit.json'), report)
    return report

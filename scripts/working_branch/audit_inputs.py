"""Independent frozen-input, proposal-index and loaded-class checks; no decoding."""
from urllib.parse import urlparse, unquote
import numpy as np
from common import *


def weak(a, b):
    return all(x <= y for x, y in zip(a, b))


def dominates(a, b):
    return weak(a, b) and any(x < y for x, y in zip(a, b))


def keep(role, child, parent, dominated):
    if role == 'CENTER':
        return weak(child, parent) or not dominated
    return child[{'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}[role]] < parent[{'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}[role]]


def loaded(root, identities):
    old, new = read(SUPPORT/'build/identity.json'), read(root/'build-02/identity.json')
    bases = {str(SUPPORT/'build/classes'): old['classes'], str(root/'build-02/classes'): new['classes']}
    bases.update({p: v for p, v in old['dependencies'].items() if isinstance(v, dict)})
    checked = 0
    for name, meta in identities.items():
        if not isinstance(meta, dict):
            continue
        assert meta['resource'].startswith('file:'), name
        path = Path(unquote(urlparse(meta['resource']).path))
        expected = next((v[str(path.relative_to(Path(p)))] for p, v in bases.items()
                         if path.is_relative_to(Path(p))), None)
        assert expected is not None and sha(path) == meta['sha256'] == expected, name
        checked += 1
    return checked


def verify(root):
    gate = read(root/'prepared-gate.json')
    assert sha(root/'protocol.md') == gate['protocolSHA256']
    for name, digest in gate['preparedHashes'].items():
        assert sha(root/'prepared'/name) == digest, name
    cases, entries, models, catalog = sources()
    actual = read(root/'prepared/cases.json')
    plans = rows(root/'prepared/schedule.jsonl')
    prior = {r['id']: r for p in sorted((FA/'paid').glob('*/evaluations.jsonl')) for r in stream(p)}
    queries = {r['id']: r for r in stream(FA/'prepared/queries.jsonl')}
    archives = read(root/'prepared/archives.json')
    for context, entry in entries.items():
        expected = nd(entry['S_archive'] + [r['objectives'] for k, r in prior.items() if queries[k]['context'] == context]
                      + [c[t]['objectives'] for c in cases if c['context'] == context for t in ('P', 'Q', 'R')])
        assert np.array_equal(expected, archives[context])
    expected_plans, expected_seeds = [], []
    for original, c in zip(cases, actual):
        assert c == dict(original, id=original['context']+'-'+original['role'])
        free = {p['slot']: p for p in entries[c['context']]['S'] if p['family'] == -1}
        assert c['P'] == {k: free[c['parentSlot']][k] for k in c['P']}
        assert c['R'] == {k: free[c['ordinaryOtherSlot']][k] for k in c['R']}
        q = prior[c['chosenId']]
        assert queries[c['chosenId']]['arm'] == 'POST_FA'
        assert all(c['Q'][k] == q[k] for k in (*FIELDS, 'resources', 'keys', 'objectives'))
        p, q = c['P']['objectives'], c['Q']['objectives']
        assert not weak(p, q) and not weak(q, p)
        assert not any(weak(s['objectives'], q) for s in entries[c['context']]['S'])
        assert not keep(c['role'], q, p, any(dominates(a, q) for a in archives[c['context']]))
        eligible = [slot for slot in free if slot != c['parentSlot']]
        for tag in ('P', 'Q', 'R'):
            seed = dict(c[tag], id=c['id']+'-'+tag)
            assert all(seed[k] == v for k, v in encode(seed['resources'], seed['keys'], catalog).items())
            assert any(weak(a, seed['objectives']) for a in archives[c['context']])
            expected_seeds.append(seed)
        for branch, length in ((0, 31), (1, 15)):
            order = list(range(199)); rng(c['id'], branch, 'fos-order').shuffle(order)
            draw = rng(c['id'], branch, 'donor-indices')
            for step, node in enumerate(order[:length]):
                expected_plans.append(dict(case=c['id'], context=c['context'], branch=branch, step=step,
                    node=node, donorSlot=draw.choice(eligible), mask=models[c['context']]['subsets'][node]))
    assert actual and len(actual) == 12 and plans == expected_plans
    assert rows(root/'prepared/seeds.jsonl') == expected_seeds
    identity = read(root/'build-02/identity.json')
    assert sha(SUPPORT/'build/identity.json') == identity['frozenDependencyIdentitySHA256']
    for path, digest in identity['inputHashes'].items():
        assert sha(path) == digest
    for name, digest in identity['sources'].items():
        path = root/('source-02' if name == 'WorkingBranchRun.java' else 'source')/name
        assert sha(path) == digest
    for name, digest in identity['classes'].items():
        assert sha(root/'build-02/classes'/name) == digest
    qa = read(root/'qa/receipt.json')
    assert (qa['attemptedQA'], qa['passedQA'], qa['failedQA']) == (36, 36, 0)
    assert qa['exactBits'] and qa['pending'] is None and qa['error'] is None
    result = dict(passed=True, cases=12, seedVectors=36, proposals=552,
                  loadedQAClasses=loaded(root, qa['loaded']), newDecoderCalls=0)
    write(root/'prepared-independent-audit.json', result)
    print('PREPARED_INDEPENDENT_AUDIT_PASSED', flush=True)


if __name__ == '__main__':
    linux(); verify(Path(sys.argv[1]))

"""Linux-only, zero-evaluation extraction of actual first-batch parent/child pairs."""
import argparse
from collections import Counter
from itertools import groupby
import hashlib
import json
from pathlib import Path
import platform
import shutil

ROLES = ['MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST']
COUNTS = dict(zip(ROLES, [15, 55, 15, 15]))


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def factories_by_job(row):
    return dict(zip(map(int, row[6].split(',')), map(int, row[7].split(','))))


def extract(source, root, stem, seed):
    folder = source / 'capture' / stem / str(seed)
    meta = read(folder / 'capture.json')
    lines = (folder / 'points.tsv').read_text().splitlines()
    rows = [line.split('\t') for line in lines]
    assert len(rows) == 5100 and all(len(r) == 10 for r in rows)
    parents, proposals = rows[:100], rows[100:]
    assert [r[0] for r in parents] == ['P'] * 100
    assert Counter(r[3] for r in parents) == COUNTS
    assert Counter(int(r[4]) for r in parents) == {-1: 80, 0: 5, 1: 5, 2: 5, 3: 5}
    assert [r[3] for r in parents] == [role for role in ROLES for _ in range(COUNTS[role])]
    assert all(int(r[1]) == i and int(r[2]) == meta['beforeGlobalFE'] for i, r in enumerate(parents))
    assert all(r[0] in ('G', 'S') and int(r[1]) == i and
               int(r[2]) == meta['beforeGlobalFE'] + i + 1 for i, r in enumerate(proposals))
    blocks = [(role, list(group)) for role, group in groupby(proposals, key=lambda row: row[3])]
    assert sorted(role for role, block in blocks) == sorted(ROLES)
    first = {}
    for role, block in blocks:
        assert len(block) == 50 * COUNTS[role]
        first[role] = iter(block[:COUNTS[role]])
    children, pairs = [], []
    for index, parent in enumerate(parents):
        child = next(first[parent[3]])
        assert parent[3:5] == child[3:5]
        if int(parent[4]) >= 0:
            assert factories_by_job(parent) == factories_by_job(child)
        pairs.append(dict(parentIndex=index, childIndex=int(child[1]), childPaidByFE=int(child[2]),
                          role=child[3], family=int(child[4]), source=child[0], batch=0))
        copy = child.copy(); copy[0:2] = ['C', str(index)]; children.append(copy)
    out = root / 'inputs' / stem / str(seed)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'points.tsv').write_text('\n'.join('\t'.join(r) for r in parents + children) + '\n')
    shutil.copyfile(folder / 'background.tsv', out / 'background.tsv')
    shutil.copyfile(folder / 'background.json', out / 'background.json')
    value = dict(passed=True, instance=stem, seed=seed, sourceCapture=str(folder),
                 sourceSHA256=sha(folder / 'points.tsv'), extractedSHA256=sha(out / 'points.tsv'),
                 backgroundSHA256=sha(out / 'background.tsv'), beforeGlobalFE=meta['beforeGlobalFE'],
                 afterGlobalFE=meta['afterGlobalFE'], roleExecutionOrder=[b[0] for b in blocks],
                 pairs=pairs, sharedFirstBatch=sum(p['source'] == 'S' for p in pairs),
                 duplicateFiltering=False, newSourceFE=0, newDecoderCalls=0,
                 qualification='Sequential role-first batches, not synchronously generated C100; all available by POST_GLOBAL A0')
    write(out / 'selection-source.json', value)
    return {k: v for k, v in value.items() if k != 'pairs'}


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.root / 'protocol.json')
    assert read(args.source / 'delivery-acceptance.json')['passed']
    results = [extract(args.source, args.root, s, seed)
               for s in plan['instances'] for seed in plan['seeds']]
    write(args.root / 'source-acceptance.json', dict(passed=True, contexts=results,
          newSearchFE=0, newDecoderCalls=0, mappingBasis='Frozen pre(groups) and first global(group) iteration order before batch selection'))
    print(json.dumps(results), flush=True)


if __name__ == '__main__':
    main()

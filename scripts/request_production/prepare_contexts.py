"""Validate real requests and prepare the predeclared conditional contexts on Linux."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import time
import numpy as np
from common import SOURCE, linux, read, sha, write


def jsonlines(path):
    with path.open() as stream:
        yield from (json.loads(line) for line in stream)


def close(a, b):
    assert np.allclose(a, b, rtol=1e-12, atol=1e-10), (a, b)


def score(record, request):
    return (record['objectives'][1]/request['energyScale'] +
            request['eta']*record['objectives'][2]/request['wageScale'])


def request_check(row, fixed):
    parent = row['parent']
    close(row['cap'], parent['objectives'][0]*[.9, 1, 1.1][row['cycle']//3])
    assert row['eta'] == [0, 1, 4][row['cycle']%3]
    assert dict(zip(parent['JS'], parent['FA'])) == fixed
    local = [f['record']['objectives'] for f in parent['factories']]
    close(parent['objectives'], [max(v[0] for v in local), sum(v[1] for v in local), sum(v[2] for v in local)])
    chosen, missing = [], []
    for pool in row['pools']:
        f = pool['factory']; records = pool['records']
        assert 0 < len(records) <= 8
        jobs = {j for j, factory in fixed.items() if factory == f}
        for record in records:
            assert set(record['jobs']) == jobs and len(record['jobs']) == len(jobs)
            assert record['paidByFE'] == row['paidFE']
            assert record['paidFE'] <= row['paidFE']
        feasible = [i for i, r in enumerate(records) if r['objectives'][0] <= row['cap']]
        index = min(feasible, key=lambda i: score(records[i], row)) if feasible else -1
        assert index == pool['chosenIndex'], 'Original selector mismatch'
        if index < 0:
            missing.append(f)
        else:
            assert pool['chosen'] == records[index]
            chosen.append(records[index])
    assert row['feasible'] == (not missing)
    combined = None
    if not missing:
        combined = [max(v['objectives'][0] for v in chosen),
                    sum(v['objectives'][1] for v in chosen),
                    sum(v['objectives'][2] for v in chosen)]
        close(row['combinedObjectives'], combined)
        assert row['outcome'] in ('PROPOSED', 'DUPLICATE_PARENT')
    else:
        assert row['outcome'] == 'INFEASIBLE'
    return dict(request=row['requestOrdinal'], family=row['family'], cycle=row['cycle'],
        paidFE=row['paidFE'], outcome=row['outcome'], cap=row['cap'], eta=row['eta'],
        missingFactories=missing, missingCount=len(missing),
        category=('no-cap-gap' if not missing else 'single-factory-cap-gap' if len(missing)==1 else 'multiple-factory-cap-gap'),
        combinedObjectives=combined)


def scalar_line(row):
    parent = row['parent']
    values = [row['requestOrdinal'], row['family'], row['cap'], row['eta'],
              row['energyScale'], row['wageScale']]
    values += [','.join(map(str, parent[k])) for k in ('objectives','JS','FA','MA','WA')]
    return '\t'.join(map(str, values)) + '\n'


def write_context(root, spec, index, row, effective, capture):
    folder = root/'inputs-v2'/spec['instance']/str(spec['seed'])/str(index)
    folder.mkdir(parents=True, exist_ok=False)
    lines = (capture/'points.tsv').read_text().splitlines()[:100]
    (folder/'points.tsv').write_text('\n'.join(lines)+'\n')
    for name in ('background.tsv','background.json'):
        shutil.copyfile(capture/name, folder/name)
    (folder/'request.tsv').write_text(scalar_line(row))
    (folder/'effective-request.tsv').write_text(scalar_line(effective))
    pool_lines=[]
    for pool in row['pools']:
        for record in pool['records']:
            values=[pool['factory'],record['paidFE']]
            values += [','.join(map(str,record[k])) for k in ('objectives','jobs','machines','workers')]
            pool_lines.append('\t'.join(map(str,values)))
    (folder/'pools.tsv').write_text('\n'.join(pool_lines)+'\n')
    write(folder/'provenance.json', dict(instance=spec['instance'], seed=spec['seed'],
        requestIndex=index, family=spec['family'], targetRequest=row['requestOrdinal'],
        shuffledRequest=effective['requestOrdinal'], targetFE=row['paidFE'],
        shuffledFE=effective['paidFE'], commonInformationBarrier=spec['after'],
        requestSourceSHA256=sha(capture/'requests.jsonl'),
        identicalCapAfterShuffle=row['cap']==effective['cap'],
        noFutureRelativeToBarrier=max(row['paidFE'],effective['paidFE'])<=spec['after']))
    return str(folder.relative_to(root))


def one(root, spec):
    capture=root/'capture'/spec['instance']/str(spec['seed'])
    assert read(root/'sources'/spec['instance']/str(spec['seed'])/'equivalence.json')['passed']
    data=list(jsonlines(capture/'requests.jsonl'))
    header, requests=data[0],data[1:]
    assert header['type']=='request-capture-metadata'
    assert len(requests)==100 and Counter(r['family'] for r in requests)=={0:25,1:25,2:25,3:25}
    parents=[line.split('\t') for line in (capture/'points.tsv').read_text().splitlines()[:100]]
    fixed={}
    for p in parents:
        family=int(p[4])
        if family>=0:
            mapping=dict(zip(map(int,p[6].split(',')),map(int,p[7].split(','))))
            if family in fixed:assert mapping==fixed[family]
            fixed[family]=mapping
    start=requests[0]['requestOrdinal']; diagnostics=[]
    for i,row in enumerate(requests):
        assert row['requestOrdinal']==start+i and row['captureOrdinal']==i+1
        assert spec['before']<=row['paidFE']<=spec['after']
        diagnostics.append(request_check(row,fixed[row['family']]))
    # Independently recover every request-time A0 from the original paid admission
    # stream. No new decoding and no future evaluations enter these snapshots.
    sys.path.insert(0,str(SOURCE/'analysis-code'))
    from audit_replay import ParetoLedger, sorted_points
    ledger=ParetoLedger(np.empty((0,3)))
    stream=iter(jsonlines(SOURCE/'sources'/spec['instance']/str(spec['seed'])/'stage-events.jsonl'))
    pending=next(stream,None)
    for request in requests:
        while pending is not None and pending['fe']<=request['paidFE']:
            if pending['kind']=='admission':ledger.offer(pending['point']['objectives'])
            pending=next(stream,None)
        assert sorted_points(ledger.points)==sorted_points(request['A0'])
    family_requests=[r for r in requests if r['family']==spec['family']]
    selected=[next(r for r in family_requests if r['cycle']==cycle) for cycle in (0,4,8)]
    outputs=[write_context(root,spec,i,row,selected[(i+1)%3],capture) for i,row in enumerate(selected)]
    return dict(instance=spec['instance'],seed=spec['seed'],family=spec['family'],
        requestCount=len(requests), categories=dict(Counter(d['category'] for d in diagnostics)),
        sampled=[d for d in diagnostics if d['request'] in {r['requestOrdinal'] for r in selected}],
        contexts=outputs, allRequestTimeArchivesExact=True,
        independentNewSearchFE=0, independentNewDecodes=0)


def main(root):
    linux();start=time.perf_counter()
    amendment=read(root/'amendment-01.json')
    assert amendment['requestCycles']==[0,4,8] and amendment['probeFEAtAmendment']==0
    specs=read(root/'source-protocol.json')['contexts']
    results=[one(root,spec) for spec in specs]
    write(root/'request-audit-v2.json',dict(passed=True,contexts=results,
        totalRealRequests=sum(r['requestCount'] for r in results),
        sampledRequests=sum(len(r['sampled']) for r in results),
        seconds=time.perf_counter()-start,newSearchFE=0,newDecodes=0))
    print('REQUEST_AUDIT_PASS',sum(r['requestCount'] for r in results),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    main(parser.parse_args().root)

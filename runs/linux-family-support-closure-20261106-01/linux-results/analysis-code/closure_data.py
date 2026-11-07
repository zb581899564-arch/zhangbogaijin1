"""Audit paid rows, retain local Pareto states, and form conditional Cartesian closures."""
import numpy as np
from common import SOURCE,read,lines
from structure import physical
from frontier import objective_powers,encode,decode,pareto,close


def oracle_records(root,seed):
    folder=root/'contexts/20_8_5_1'/str(seed);points=read(folder/'before.json')
    definitions=[list(lines(folder/f'factory-{f}.jsonl')) for f in range(5)]
    paid=list(lines(root/'science'/str(seed)/'paid.jsonl'))
    inputs=(folder/'cases.tsv').read_text().splitlines();assert len(paid)==len(inputs)
    factors=[[] for _ in range(5)];unchanged=0
    for i,(row,line) in enumerate(zip(paid,inputs)):
        fields=line.split('\t');assert row['id']==fields[0] and row['fe']==i+1
        for k,field in enumerate(('JS','FA','MA','WA')):assert row[field]==list(map(int,fields[k+3].split(',')))
        f=row['factory'];local=definitions[f][row['localId']]
        assert row['localId']==len(factors[f]) and f==int(fields[1]) and row['localId']==int(fields[2])
        assert physical(row,f)==tuple(zip(local['jobs'],local['machines'],local['workers']))
        for other in range(5):
            if other==f:continue
            assert physical(row,other)==physical(points[0],other)
            for key in ('factoryMakespan','factoryEnergy','factoryCost'):assert row[key][other]==points[0][key][other]
            unchanged+=1
        record=dict(local,objectives=[row[key][f] for key in ('factoryMakespan','factoryEnergy','factoryCost')])
        factors[f].append(record)
    checks=0
    for f in range(5):
        lookup={tuple(zip(r['jobs'],r['machines'],r['workers'])):r for r in factors[f]}
        for point in points:
            actual=lookup[physical(point,f)]['objectives']
            assert actual==[point[k][f] for k in ('factoryMakespan','factoryEnergy','factoryCost')]
            checks+=1
    return factors,dict(paidRows=len(paid),fullVectorsMatched=len(paid),unchangedFactoryChecks=unchanged,
        exactImportedLocalObjectiveChecks=checks)


def closure(factors):
    powers=objective_powers([r for group in factors for r in group]);reduced=[];reduction=[]
    for group in factors:
        keep=pareto([(*encode(r['objectives'],powers),i) for i,r in enumerate(group)])
        reduced.append([group[p[3]] for p in keep]);reduction.append(dict(input=len(group),retained=len(keep)))
    front,stages=close(reduced,powers)
    return dict(points=[decode(p[:3],powers) for p in front],indices=[list(p[3]) for p in front],
        factors=reduced,reduction=reduction,stages=stages,powers=powers,
        algebraicExpandedStates=sum(s['expandedStates'] for s in stages))


def context(root,seed):
    factors,audit=oracle_records(root,seed)
    structure=read(root/'contexts/20_8_5_1'/str(seed)/'structure.json')
    pool=[[r for r in structure['poolRecords'] if r['factory']==f] for f in range(5)]
    background=read(SOURCE/'inputs-v2/20_8_5_1'/str(seed)/'0/background.json')
    return dict(seed=seed,A0=background,finite=closure(factors),pool=closure(pool),audit=audit)


def witness_indices(points,gains):
    values=np.asarray(points)
    ids={0,len(points)-1,*map(int,np.argmin(values,axis=0)),*map(int,np.linspace(0,len(points)-1,3))}
    ids.update(int(np.argmax(g)) for g in gains.values())
    return sorted(ids)


def vectors(data,index):
    chosen=[data['factors'][f][j] for f,j in enumerate(data['indices'][index])]
    rows=[(j,f,m,w) for f,r in enumerate(chosen) for j,m,w in zip(r['jobs'],r['machines'],r['workers'])]
    return [list(v) for v in zip(*rows)]

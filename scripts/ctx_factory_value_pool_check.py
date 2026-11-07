"""Independent scalar reconstruction of frozen pool truncation and receiver sampling."""
import numpy as np


def dominates(a,b):
    return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))


def offer(pool,candidate,records):
    c=records[candidate];same=lambda r:all(records[r][k]==c[k] for k in ('jobs','machines','workers'))
    if any(same(r) or dominates(records[r]['objectives'],c['objectives']) for r in pool):return pool[:]
    value=[r for r in pool if not dominates(c['objectives'],records[r]['objectives'])]+[candidate]
    if len(value)<=8:return value
    objs={r:records[r]['objectives'] for r in value};low=[min(o[k] for o in objs.values()) for k in range(3)]
    high=[max(o[k] for o in objs.values()) for k in range(3)];keep=[]
    for k in range(3):
        best=min(value,key=lambda r:objs[r][k])
        if best not in keep:keep.append(best)
    while len(keep)<8:
        def distance(r):
            nearest=float('inf')
            for selected in keep:
                total=0.
                for k in range(3):
                    v=(objs[r][k]-objs[selected][k])/max(1e-12,high[k]-low[k]);total+=v*v
                nearest=min(nearest,total)
            return nearest
        keep.append(max((r for r in value if r not in keep),key=distance))
    return keep


def centered_ids(tokens,points,uniform):
    def order(ids):
        x=np.array([points[pid]['objectives'] for pid,_ in ids])
        d=np.all(x[:,None,:]<=x[None,:,:],axis=2)&np.any(x[:,None,:]<x[None,:,:],axis=2)
        f=d.sum(axis=0)+1./(d.sum(axis=1)+1)
        return [ids[i] for i in sorted(range(len(ids)),key=lambda i:f[i])]
    result=[]
    for family in (-1,0,1,2,3):
        ids=[p for p in tokens if p[1]==family];take=11 if family==-1 else 1
        for k in range(3):
            ids=order(ids) if uniform else sorted(ids,key=lambda p:points[p[0]]['objectives'][k])
            ids=ids[take:]
        ids=order(ids);result.extend(((ids[0][0],str(family),'FIRST'),(ids[-1][0],str(family),'LAST')))
    return result


def check_pools(evidence,points,records,queries):
    from ctx_role_factory_contract import factory_parts
    libraries={(s,k):{} for s in ('S','U') for k in ('WHOLE_FA','JOBSET')};inputs={};checked=0;request_count=0

    def key(pid,f,schema):
        assignment,parts=factory_parts(points[pid])
        return f,assignment if schema=='WHOLE_FA' else tuple(sorted(parts[f][1]))

    for line in (evidence/'events.tsv').read_text('utf-8').splitlines():
        source,phase,cycle,fe,raw=line.split('\t');cycle,fe=int(cycle),int(fe)
        if phase=='QUERY':
            unique={}
            for s in ('S','U'):
                for pid,family,which in centered_ids(inputs[s],points,s=='U'):
                    physical=tuple(part[2] for part in factory_parts(points[pid])[1]);cap=points[pid]['objectives'][0]
                    unique.setdefault((physical,cap),[]).append([pid,family,f'{s}:{family}:{which}'])
            for aliases in unique.values():
                request_count+=1;qid=f'q{request_count:03d}';parent=aliases[0][0];cap=points[parent]['objectives'][0]
                for s in ('S','U'):
                    for schema in ('WHOLE_FA','JOBSET'):
                        expected=[];missing=[]
                        for f in range(3):
                            old=libraries[s,schema].get(key(parent,f,schema))
                            if old is None:missing.append(f)
                            pool=offer(old or [],parent+'#'+str(f),records)
                            expected.append(sorted(r for r in pool if records[r]['objectives'][0]<=cap))
                        actual=queries[qid,s,schema]
                        assert actual['aliases']==aliases and actual['parent']==parent and actual['cycle']==cycle and actual['fe']==fe
                        assert actual['pool']==expected and actual['missingFactoryContexts']==missing
                        checked+=1
        else:
            tokens=[(p.split(':')[0],int(p.split(':')[1])) for p in raw.split(',')]
            if phase=='PRE_GLOBAL':inputs[source]=tokens;continue
            for schema in ('WHOLE_FA','JOBSET'):
                cache=libraries[source,schema];live=set()
                for pid,_ in tokens:
                    for f in range(3):
                        k=key(pid,f,schema);live.add(k);cache[k]=offer(cache.get(k,[]),pid+'#'+str(f),records)
                if phase=='SURVIVORS':
                    for k in list(cache):
                        if k not in live:del cache[k]
    assert checked==len(queries)
    return dict(independentlyRebuiltRequests=request_count,independentlyRebuiltCases=checked,
                samplingPoolDominanceTruncationCapFallbackAndLivenessEqual=True)

"""Physical signatures and exact inherited fragments, independent of global interleaving."""
from collections import Counter
import numpy as np


def describe(point, catalog):
    inverse={tuple(v):i for i,v in enumerate(catalog)}
    resource=[None]*len(point['JS']);chains=[[] for _ in range(max(t[0] for t in catalog)+1)]
    for j,f,m,w in zip(*(point[k] for k in ('JS','FA','MA','WA'))):
        resource[j]=inverse[f,m,w];chains[f].append(j)
    assert all(r is not None for r in resource) and all(chains)
    point['_r']=tuple(resource);point['_fa']=tuple(catalog[r][0] for r in resource)
    point['_chains']=tuple(map(tuple,chains));point['_physical']=(point['_r'],point['_chains'])
    # Encode directed same-factory job/resource pairs. A pair is an observed within-chain
    # precedence fragment; its presence alone does not prove an entire compatible schedule.
    size=len(catalog);width=len(resource)*size;codes=[j*size+r for j,r in enumerate(resource)]
    point['_single']=frozenset(codes)
    point['_pairs']=frozenset(codes[a]*width+codes[b] for chain in chains
                             for i,a in enumerate(chain) for b in chain[i+1:])
    return point


def feature_sets(points):
    return dict(physical={p['_physical'] for p in points}, FA={p['_fa'] for p in points},
                resources={p['_r'] for p in points},
                singles=set().union(*(p['_single'] for p in points)),
                orderedPairs=set().union(*(p['_pairs'] for p in points)))


def retention(before, after):
    a,b=feature_sets(before),feature_sets(after)
    return {name:dict(before=len(a[name]),after=len(b[name]),retained=len(a[name]&b[name]),
                     lost=len(a[name]-b[name]),added=len(b[name]-a[name]),
                     retainedFraction=len(a[name]&b[name])/len(a[name]) if a[name] else None) for name in a}


def fa_geometry(points):
    fa=np.asarray([p['_fa'] for p in points]);n,jobs=fa.shape
    co=np.mean(fa[:,:,None]==fa[:,None,:],axis=0)
    upper=co[np.triu_indices(jobs,1)]
    entropy=np.zeros_like(upper);inside=(upper>0)&(upper<1);p=upper[inside]
    entropy[inside]=-p*np.log2(p)-(1-p)*np.log2(1-p)
    unique=len({p['_fa'] for p in points});counts=Counter(p['_fa'] for p in points)
    return dict(members=n,uniqueFA=unique,maxIdenticalFA=max(counts.values()),
                meanCoassignment=float(upper.mean()),meanPairBinaryEntropy=float(entropy.mean()),
                exactConstantPairs=int(np.count_nonzero((upper==0)|(upper==1)))),upper


def pair_motion(before, after):
    _,a=fa_geometry(before);_,b=fa_geometry(after)
    return dict(meanAbsoluteCoassignmentChange=float(np.abs(a-b).mean()),
                correlation=float(np.corrcoef(a,b)[0,1]) if a.std() and b.std() else None)


def cohort(points):
    return dict(all=fa_geometry(points)[0],free=fa_geometry([p for p in points if p.get('family',-1)==-1])[0])


def json_safe(value):
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items() if not k.startswith('_')}
    if isinstance(value,list):return [json_safe(v) for v in value]
    return value

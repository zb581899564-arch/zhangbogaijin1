"""Low-memory labelled orthant geometry and leave-origin-out IGD+, no schedule scoring."""
import numpy as np


def covered_by(front,other):
    a,b=np.asarray(front,float).reshape(-1,3),np.asarray(other,float).reshape(-1,3)
    return np.array([bool(np.any(np.all(b<=p,axis=1))) for p in a],bool)


def origin_hv(front,labels,other,reference=1.5):
    """Exact x/y slab sweep: all per-origin single-supply and leave-one-origin-out HV gaps."""
    a,b=np.asarray(front,float).reshape(-1,3),np.asarray(other,float).reshape(-1,3)
    names=list(dict.fromkeys(labels));k=len(names);assert k and len(labels)==len(a)
    ids=np.array([names.index(s) for s in labels]);r=float(reference)
    # B remains in every comparison: points it covers can never change any measured gap.
    keep=np.all(a<r,axis=1)&~covered_by(a,b);a,ids=a[keep],ids[keep]
    b=b[np.all(b<r,axis=1)]
    p=np.vstack([a,b]);category=np.r_[ids,np.full(len(b),k,int)]
    if not len(p):
        return dict(poolHV=0.,otherHV=0.,novelHV=0.,standalone={s:0. for s in names},exclusive={s:0. for s in names})
    ys=np.unique(p[:,1]);dy=np.diff(np.r_[ys,r]);yi=np.searchsorted(ys,p[:,1])
    order=np.argsort(p[:,0],kind='stable');p,category,yi=p[order],category[order],yi[order]
    xs,starts=np.unique(p[:,0],return_index=True);ends=np.r_[starts[1:],len(p)]
    direct=np.full((k+1,len(ys)),r);standalone=np.zeros(k);exclusive=np.zeros(k);total=base=0.
    for index,(x,start,end) in enumerate(zip(xs,starts,ends)):
        for t in range(start,end):direct[category[t],yi[t]]=min(direct[category[t],yi[t]],p[t,2])
        z=np.minimum.accumulate(direct,axis=1);ranked=np.partition(z,1,axis=0);lowest,second=ranked[0],ranked[1]
        dx=(xs[index+1] if index+1<len(xs) else r)-x
        total+=dx*float(np.dot(r-lowest,dy));base+=dx*float(np.dot(r-z[k],dy))
        standalone+=dx*np.maximum(z[k]-z[:k],0.).dot(dy)
        unique_gap=(second-lowest)*dy
        exclusive+=dx*((z[:k]==lowest)*unique_gap).sum(axis=1)
    assert sum(exclusive)<=total-base+2e-10 and min(exclusive)>=-1e-12
    return dict(poolHV=float(total),otherHV=float(base),novelHV=float(total-base),
                standalone={s:float(v) for s,v in zip(names,standalone)},exclusive={s:float(v) for s,v in zip(names,exclusive)})


def origin_igd(front,labels,reference):
    a=np.asarray(front,float);ref=np.asarray(reference,float);names=list(dict.fromkeys(labels));k=len(names)
    ids=np.array([names.index(s) for s in labels]);totals=np.zeros(k);closest=np.zeros(k,int);tied=0;total=0.
    for start in range(0,len(ref),128):
        delta=np.maximum(a[None,:,:]-ref[start:start+128,None,:],0.)
        distances=np.sqrt((delta*delta).sum(axis=2));profiles=np.vstack([distances[:,ids==i].min(axis=1) for i in range(k)])
        best=profiles.min(axis=0);total+=float(best.sum());ties=(profiles==best)
        unique=ties.sum(axis=0)==1;closest+=(ties&unique).sum(axis=1);tied+=int((~unique).sum())
        for i in range(k):
            if k>1:totals[i]+=float((np.delete(profiles,i,axis=0).min(axis=0)-best).sum())
    return dict(IGDplus=total/len(ref),referenceSize=len(ref),uniqueNearestReferencePoints={s:int(v) for s,v in zip(names,closest)},
        tiedNearestOriginReferencePoints=tied,leaveOutIncrease={s:float(v/len(ref)) if k>1 else None for s,v in zip(names,totals)})


def fixtures():
    from itertools import combinations
    def brute(points,r):
        points=[p for p in points if all(x<r for x in p)];value=0.
        for count in range(1,len(points)+1):
            for group in combinations(points,count):value+=(-1)**(count+1)*float(np.prod(r-np.max(group,axis=0)))
        return value
    examples=[([[.2,.7,.5],[.5,.2,.4],[.3,.4,.8]],['M','C','C'],[[.4,.4,.4]]),
              ([[.2,.2,.2],[.2,.2,.2],[.4,.4,.4]],['M','C','W'],[[.3,.3,.3]]),
              ([[.2,.7,.5],[1.2,.2,.4]],['M','C'],[]),
              ([[.5,.5,.5]],['M'],[[.2,.2,.2]]),
              ([[1.1,.1,.1]],['M'],[[1.2,.2,.2]])]
    for a,labels,b in examples:
        r=1.;out=origin_hv(a,labels,b,r);pool=brute(a+b,r);base=brute(b,r)
        assert abs(out['poolHV']-pool)<1e-12 and abs(out['otherHV']-base)<1e-12
        for s in set(labels):
            assert abs(out['standalone'][s]-(brute(b+[p for p,t in zip(a,labels) if t==s],r)-base))<1e-12
            assert abs(out['exclusive'][s]-(pool-brute(b+[p for p,t in zip(a,labels) if t!=s],r)))<1e-12
    return dict(cases=len(examples),method='Independent inclusion-exclusion, including ties, dominated/box-excluded points and empty B',passed=True)

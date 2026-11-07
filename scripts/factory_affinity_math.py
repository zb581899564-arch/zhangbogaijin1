"""Exact capacity-preserving linear assignment versus complete steepest two-job exchanges."""
from itertools import permutations
import numpy as np
from scipy.optimize import linear_sum_assignment


def value(cost,assignment):
    return float(cost[np.arange(len(assignment)),assignment].sum())


def exact(cost,initial):
    slots=np.repeat(np.arange(cost.shape[1]),np.bincount(initial,minlength=cost.shape[1]))
    row,column=linear_sum_assignment(cost[:,slots]);out=np.empty_like(initial);out[row]=slots[column]
    assert np.array_equal(np.bincount(out,minlength=cost.shape[1]),np.bincount(initial,minlength=cost.shape[1]))
    return out


def swap_descent(cost,initial):
    assignment=initial.copy();n=len(initial);iterations=0
    tolerance=1e-10*max(1.,float(np.max(np.abs(cost))))
    upper=np.triu(np.ones((n,n),dtype=bool),1)
    while True:
        old=cost[np.arange(n),assignment]
        delta=cost[:,assignment]+cost[:,assignment].T-old[:,None]-old[None,:]
        delta=np.where(upper & (assignment[:,None]!=assignment[None,:]),delta,np.inf)
        i,j=np.unravel_index(np.argmin(delta),delta.shape)
        if delta[i,j]>=-tolerance:return assignment,iterations,float(delta[i,j])
        assignment[i],assignment[j]=assignment[j],assignment[i];iterations+=1
        if iterations>n*n*cost.shape[1]:raise RuntimeError('Unexpected swap descent guard reached')


def cycles(cost,initial,target):
    unused={int(j) for j in np.flatnonzero(initial!=target)};result=[]
    while unused:
        first=min(unused);start=int(initial[first]);job=first;path=[]
        while True:
            unused.remove(job);path.append(job);next_factory=int(target[job])
            if next_factory==start:break
            options=[j for j in unused if initial[j]==next_factory]
            if not options:raise AssertionError('Unbalanced assignment cycle')
            job=min(options)
        delta=float(sum(cost[j,target[j]]-cost[j,initial[j]] for j in path))
        result.append({'jobs':path,'oldFactory':[int(initial[j]) for j in path],
                       'newFactory':[int(target[j]) for j in path],'delta':delta})
    assert abs(sum(c['delta'] for c in result)-(value(cost,target)-value(cost,initial)))<1e-8*max(1.,abs(value(cost,initial)))
    return result


def checks():
    rng=np.random.default_rng(12570003);initial=np.array([0,0,1,1,2,2]);all_assignments=set(permutations(initial))
    for _ in range(16):
        cost=rng.uniform(1,10,(6,3));solution=exact(cost,initial)
        expected=min(value(cost,np.asarray(a)) for a in all_assignments)
        assert abs(value(cost,solution)-expected)<1e-10
        local,_,residual=swap_descent(cost,initial)
        assert residual>=-1e-9 and value(cost,local)>=expected-1e-10
        cycles(cost,local,exact(cost,local))
    # A real 3-cycle improvement hidden from every pair exchange: each individual trade is costly.
    cost=np.array([[1.,0.,3.],[3.,1.,0.],[0.,3.,1.]])
    local,steps,_=swap_descent(cost,np.array([0,1,2]));target=exact(cost,local)
    assert steps==0 and value(cost,target)==0 and any(len(c['jobs'])==3 and c['delta']<0 for c in cycles(cost,local,target))
    return {'status':'PASS','enumeratedFixtures':16,'assignmentsPerFixture':len(all_assignments),'threeCycleWitness':True,'decoderCalls':0}

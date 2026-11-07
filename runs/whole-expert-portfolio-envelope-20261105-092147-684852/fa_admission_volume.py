"""Numeric-only 3D sweep for admission logs; independently checked against the existing HV kernel."""
from bisect import bisect_left
import numpy as np


def volume(points,reference=(1.5,1.5,1.5)):
    ref=np.asarray(reference,dtype=float);values=np.asarray(points,dtype=float).reshape(-1,3)
    assert np.all(values>=0) and np.all(ref>0)
    values=values[np.all(values<ref,axis=1)]
    if not len(values):return 0.
    values=values[np.lexsort((values[:,2],values[:,1],values[:,0]))]
    ys,zs=[],[];area=0.;total=0.;previous_x=0.
    for x,y,z in values:
        total+=(x-previous_x)*area;previous_x=x
        index=bisect_left(ys,y)
        if index and zs[index-1]<=z:continue
        if index<len(ys) and ys[index]==y and zs[index]<=z:continue
        old_z=zs[index-1] if index else ref[2];last_y=y;end=index;gain=0.
        while end<len(ys) and zs[end]>=z:
            gain+=(ys[end]-last_y)*(old_z-z);last_y=ys[end];old_z=zs[end];end+=1
        next_y=ys[end] if end<len(ys) else ref[1]
        gain+=(next_y-last_y)*(old_z-z)
        area+=gain;ys[index:end]=[y];zs[index:end]=[z]
    return float(total+(ref[0]-previous_x)*area)


def checks(independent):
    rng=np.random.default_rng(12680003);worst=0.
    cases=[np.empty((0,3)),np.array([[.2,.7,.5],[.5,.2,.4],[.3,.4,.8],[.2,.7,.5]]),
           np.array([[0,0,0],[1.5,0,0],[.1,2,.2]])]
    cases.extend(rng.uniform(0,2,(int(rng.integers(1,25)),3)) for _ in range(64))
    for points in cases:
        for ref in (1.25,1.5,2.):
            error=abs(volume(points,(ref,)*3)-independent(points,(ref,)*3));worst=max(worst,error)
            assert error<1e-11
    return {'status':'PASS','numericFrontFixtures':len(cases),'references':3,'maxAbsoluteError':worst,'searchFE':0,'decoderCalls':0}

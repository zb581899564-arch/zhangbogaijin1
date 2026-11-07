"""Finite-matrix certificates; exact weak dominance and conservative strict differences."""
import numpy as np
from cf_common import physical

ORDINARY={'RESOURCE':3,'ORDER':12,'JOB_A':5,'JOB_B':10}


def strict_better(a,b,tol):
    a,b=np.asarray(a),np.asarray(b)
    return bool(np.all(a<=b) and np.any(b-a>tol))


def proper(mask):
    return [m for m in range(mask) if m&mask==m]


def minimal_positive(gains,hv_tol):
    return [m for m,g in enumerate(gains) if g>hv_tol and all(gains[s]<=hv_tol for s in proper(m))]


def certificate(matrix,gains,tol,hv_tol):
    parent,full=matrix[0],matrix[15]
    fp,pp=physical(full),physical(parent)
    strict=[m for m in range(1,15) if strict_better(matrix[m]['objectives'],full['objectives'],tol)]
    equal=[m for m in range(1,15) if matrix[m]['objectives']==full['objectives']]
    new_strict=[m for m in strict if physical(matrix[m]) not in (pp,fp)]
    ordinary={name:dict(mask=m,strictBetter=strict_better(matrix[m]['objectives'],full['objectives'],tol),
                           exactEqual=matrix[m]['objectives']==full['objectives'],
                           sameParentPhysical=physical(matrix[m])==pp,
                           sameFullPhysical=physical(matrix[m])==fp)
              for name,m in ORDINARY.items()}
    needed={};minimal={}
    for name,values in gains.items():
        minimal[name]=minimal_positive(values,hv_tol)
        needed[name]=dict(fullNecessary=bool(values[15]>hv_tol and max(values[:15])<=hv_tol),
                         necessaryAtomsAtFull=[bit for bit in (1,2,4,8) if values[15]>hv_tol and values[15^bit]<=hv_tol])
    atom_harm=[bit for bit in (1,2,4,8) if strict_better(matrix[15^bit]['objectives'],full['objectives'],tol)]
    mixed_minimal=[m for m in minimal['beforeEvent'] if m.bit_count()>=2 and m&3 and m&12]
    cross_job=[m for m in mixed_minimal if m&5 and m&10]
    return dict(strictBetterSubsets=strict,strictBetterNewPhysicalSubsets=new_strict,
                equalObjectiveSubsets=equal,equalSameFullPhysical=[m for m in equal if physical(matrix[m])==fp],
                equalDifferentPhysical=[m for m in equal if physical(matrix[m])!=fp],
                ordinary=ordinary,parentStrictlyBetterThanFull=strict_better(parent['objectives'],full['objectives'],tol),
                harmfulAtomsAtFull=atom_harm,necessity=needed,minimalPositiveMasks=minimal,
                resourceOrderMinimalCertificates=mixed_minimal,crossJobResourceOrderCertificates=cross_job,
                uniquePhysical=len({physical(m) for m in matrix}),
                note='Atom effects are conditional on the other three edits. Certificates are local, not transfer evidence.')


def fixtures():
    assert proper(6)==[0,2,4]
    assert not strict_better([1,2,3],[1,2,3],np.array([1e-8]*3))
    assert not strict_better([1,2-1e-10,3],[1,2,3],np.array([1e-8]*3))
    assert strict_better([1,1,3],[1,2,3],np.array([1e-8]*3))
    assert not strict_better([1,1,3.01],[1,2,3],np.array([1e-8]*3))
    values=[0.]*16;values[5]=1.;values[15]=2.
    assert minimal_positive(values,1e-12)==[5]
    values=[0.]*16;values[15]=1.
    assert minimal_positive(values,1e-12)==[15]
    return dict(passed=True,finiteSubsetAndDominanceFixtures=7)

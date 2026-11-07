"""Fractional machine-worker assignment under a fixed FA and a three-objective target box."""
import time
import warnings
import numpy as np
from scipy.optimize import linprog,OptimizeWarning
from scipy.sparse import coo_matrix,hstack

from .dual_bound import certificate
from .prefix_state import availability,multiplier

warnings.filterwarnings('once',category=OptimizeWarning)
ROUNDING_BUDGET_INFLATION=1+1e-10


def downward(value):
    value=float(value)
    if value==0:return 0.
    for _ in range(3):value=float(np.nextafter(value,-np.inf))
    return max(0.,value)


class FixedFARelaxation:
    def __init__(self,metadata,assignment,prefix=None,horizon=None,fixed_stage_zero=None):
        self.metadata=metadata;self.assignment=tuple(assignment)
        self.prefix=prefix;self.horizon=horizon
        self.fixed_stage_zero=fixed_stage_zero
        assert len(assignment)==metadata['jobs'] and set(assignment)==set(range(len(metadata['factories'])))
        self.row_kinds=[];self.row_labels=[];self.row_constants=[];self.column_entries=[];self.groups=[]
        self._build()

    def _row(self,kind,label,constant=0.):
        index=len(self.row_kinds);self.row_kinds.append(kind);self.row_labels.append(label)
        self.row_constants.append(downward(constant));return index

    def _build(self):
        resource={}
        for f,stages in enumerate(self.metadata['factories']):
            for k,stage in enumerate(stages):
                for m in range(stage['machines']):resource[(f,k,'M',m)]=self._row(0,f'f{f}/s{k}/machine{m}',availability(self.prefix,f,k,'M',m))
                for w in range(stage['workers']):resource[(f,k,'W',w)]=self._row(0,f'f{f}/s{k}/worker{w}',availability(self.prefix,f,k,'W',w))
        chain=[self._row(0,f'job{j}/chain',self.prefix['firstCompletion'][j] if self.prefix else 0.) for j in range(self.metadata['jobs'])]
        energy=self._row(1,'totalEnergy',self.prefix['partialObjectives'][1] if self.prefix else 0.)
        labor=self._row(2,'totalLabor',self.prefix['partialObjectives'][2] if self.prefix else 0.)
        rr=[];cc=[];vv=[];eqr=[];eqc=[]
        for j,f in enumerate(self.assignment):
            for k,stage in enumerate(self.metadata['factories'][f]):
                if self.prefix and k==0 and self.prefix['completedJobs'][j]:continue
                start=len(self.column_entries);group=len(self.groups)
                for m in range(stage['machines']):
                    for w in range(stage['workers']):
                        if k==0 and self.fixed_stage_zero is not None and (m,w)!=tuple(self.fixed_stage_zero[j]):continue
                        pair=m*stage['workers']+w;factor=multiplier(self.prefix,self.metadata,self.horizon,f,k,w)
                        b=downward(stage['base'][j][pair]*factor)
                        entries=[(resource[(f,k,'M',m)],b),(resource[(f,k,'W',w)],b),(chain[j],b),
                            (energy,downward(stage['energy'][j][pair]*factor)),(labor,downward(stage['labor'][j][pair]*factor))]
                        col=len(self.column_entries);self.column_entries.append(entries)
                        for row,value in entries:rr.append(row);cc.append(col);vv.append(value)
                        eqr.append(group);eqc.append(col)
                self.groups.append((start,len(self.column_entries)))
                if self.groups[-1][0]==self.groups[-1][1]:raise ValueError('A remaining operation has no legal resource pair')
        shape=(len(self.row_kinds),len(self.column_entries))
        self.matrix=coo_matrix((vv,(rr,cc)),shape=shape).tocsc()
        eq=coo_matrix((np.ones(len(eqr)),(eqr,eqc)),shape=(len(self.groups),shape[1])).tocsc()
        self.equalities=hstack([eq,coo_matrix((len(self.groups),1))],format='csc')

    def solve(self,target):
        target=np.asarray(target,dtype=float)
        if len(target)!=3 or np.any(target<=0):raise ValueError('This diagnostic requires positive three-objective targets')
        budgets=target[np.asarray(self.row_kinds)]*ROUNDING_BUDGET_INFLATION
        matrix=hstack([self.matrix.multiply(1/budgets[:,None]),-np.ones((len(budgets),1))],format='csc')
        objective=np.r_[np.zeros(matrix.shape[1]-1),1.]
        start=time.monotonic()
        result=linprog(objective,A_ub=matrix,b_ub=-np.asarray(self.row_constants)/budgets,A_eq=self.equalities,
            b_eq=np.ones(len(self.groups)),bounds=(0,None),method='highs',
            options={'threads':1,'dual_feasibility_tolerance':1e-9,'primal_feasibility_tolerance':1e-9})
        seconds=time.monotonic()-start
        if not result.success:raise RuntimeError(f'Necessary relaxation solver failed: {result.status}: {result.message}')
        assert np.max(np.abs(result.eqlin.residual))<1e-6 and np.min(result.ineqlin.residual)>-1e-6
        bound=certificate(self,budgets,result.ineqlin.marginals)
        assert bound['lower']<=result.fun+1e-6
        return {'primalMultiplier':float(result.fun),'dual':bound,'solverSeconds':seconds,
            'variables':len(self.column_entries),'inequalityRows':len(budgets),'operationAssignmentGroups':len(self.groups)}


def engineering_checks():
    def toy(jobs,machines,workers,base,energy,labor):
        stage={'machines':machines,'workers':workers,'base':base,'energy':energy,'labor':labor}
        return {'jobs':jobs,'stages':1,'factories':[[stage]]}
    cases=[('one-job',toy(1,1,1,[[1]],[[1]],[[1]]),[1,1,1],1),
        ('tight-time',toy(1,1,1,[[1]],[[1]],[[1]]),[.5,1,1],2),
        ('parallel-capacity',toy(2,2,2,[[1]*4]*2,[[1]*4]*2,[[1]*4]*2),[1,2,2],1),
        ('joint-time-energy',toy(1,2,1,[[1,.5]],[[1,3]],[[1,.5]]),[.75,1.5,1],10/9)]
    results=[]
    for name,data,target,expected in cases:
        solved=FixedFARelaxation(data,[0]*data['jobs']).solve(target)
        assert abs(solved['primalMultiplier']-expected)<1e-7
        assert abs(solved['dual']['lower']-expected)<1e-7
        results.append({'name':name,'expected':expected,**solved})
    return results

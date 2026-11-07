"""Fixed half-JS profiles from the same previously paid representative schedules."""
import numpy as np
from .cases import SOURCE,representatives,assignment
from .relaxation import FixedFARelaxation


def make_profiles(static_plan,spec,rows):
    stem=spec['stem'];profiles=[];target_by_seed={}
    for cohort in static_plan['cohorts']:
        seed=cohort['seed'];target_by_seed[seed]=cohort['targets']
        for mode in ('STRICT_FULL','NSGA_STRICT'):
            front=rows(SOURCE/stem/str(seed)/mode/'solutions.jsonl')
            records=representatives(front,static_plan['commonEmpiricalCuts'],spec['normalization']['scale'])
            for i,record in enumerate(records):
                profiles.append({'id':f'{seed}-{mode}-{i}','seed':seed,'method':mode,'labels':record['labels'],
                    'point':record['point'],'assignment':assignment(record['point'])})
    return profiles,target_by_seed


def analytic_prefix_checks():
    stage={'machines':1,'workers':1,'base':[[1],[1]],'energy':[[1],[1]],'labor':[[1],[1]],
        'alpha':[float(np.log(2))],'mu':[0.],'beta':[1.],'h0':[0.]}
    data={'jobs':2,'stages':1,'factories':[[stage]]}
    prefix={'completedJobs':[True,False],'firstCompletion':[1.,0.],'partialObjectives':[1.,1.,1.],
        'machineEnd':[[1.]],'workerEnd':[[1.]],'workerFatigue':[[.5]]}
    result=[]
    for mode,expected,horizon in (('TIME',2/2.2,None),('FATIGUE',2.5/2.2,2.2)):
        solved=FixedFARelaxation(data,[0,0],prefix,horizon).solve([2.2]*3)
        assert abs(solved['dual']['lower']-expected)<1e-7
        assert solved['dual']['excludesTarget']==(mode=='FATIGUE')
        result.append({'mode':mode,'expected':expected,**solved})
    return result

"""Post-hoc geometry of already-paid fronts; no search, scoring API or promotion."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
import shutil
import sys
import numpy as np

from run_long_budget_bridge import read,rows,write_once
from ctx_phase_analysis import paired


def nearest(front,reference,norm):
    normalized=(np.asarray(front)-norm['lower'])/norm['scale']
    return np.asarray([np.sqrt(np.sum(np.maximum(normalized-r,0.)**2,axis=1)).min() for r in reference])


def main(root):
    assert read(root/'independent-final-audit.json')['passed']
    result=read(root/'analysis.json');plan=read(root/'protocol.json')['contract'];cases=[]
    factors=(('TASK_ONLY','NATIVE'),('ORDER_ONLY','NATIVE'),('FULL','TASK_ONLY'),('FULL','ORDER_ONLY'))
    for case in result['instances']:
        values={(v['seed'],v['arm']):v['metrics'] for v in case['observations']};pairs=[];changes=[]
        norm=case['normalization'];reference=np.asarray(case['reference'])
        for seed in plan['seeds']:
            for a,b in factors:
                pairs.append(dict(seed=seed,A=a,B=b,**paired(values[seed,a],values[seed,b]),descriptiveOnly=True))
            for mode in plan['modes']:
                evidence=read(root/case['instance']/str(seed)/('FE-'+mode)/'role-mapping-audit.json')
                events=rows(root/case['instance']/str(seed)/('FE-'+mode)/'role-events.jsonl')
                per_generation=[dict(generation=e['generation'],roleChanges=sum(a['role']!=b['role'] for a,b in zip(e['before'],e['after'])),
                    visitPositionChanges=sum(i!=v for i,v in enumerate(e['visit']))) for e in events]
                changes.append(dict(seed=seed,mode=mode,**evidence,perGeneration=per_generation))
        geometry=[]
        for row in case['comparisons']:
            for seed in plan['seeds']:
                a,b=values[seed,row['A']],values[seed,row['B']]
                da,db=nearest(a['front'],reference,norm),nearest(b['front'],reference,norm)
                assert abs(float(da.mean())-a['IGDplus'])<2e-12 and abs(float(db.mean())-b['IGDplus'])<2e-12
                geometry.append(dict(seed=seed,A=row['A'],B=row['B'],referenceSize=len(reference),
                    primaryCloserReferencePoints=int(np.sum(da<db)),opponentCloserReferencePoints=int(np.sum(db<da)),equalDistanceReferencePoints=int(np.sum(da==db)),
                    primaryObjectiveMin=np.min(a['front'],axis=0).tolist(),opponentObjectiveMin=np.min(b['front'],axis=0).tolist(),
                    primaryFrontSize=len(a['front']),opponentFrontSize=len(b['front']),
                    primaryMeanIGDplusDistance=float(da.mean()),opponentMeanIGDplusDistance=float(db.mean())))
        cases.append(dict(instance=case['instance'],factorComparisons=pairs,roleAndVisitChanges=changes,referenceGeometry=geometry))
    write_once(root/'posthoc-geometry.json',dict(instances=cases,descriptiveOnly=True,newSearchFE=0,newDecoderCalls=0,
        noCausalAttributionOrControlPromotion=True,originalStopUnchanged=True,goalAchieved=False))
    folder=root/'posthoc-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('PA_ROLE_POSTHOC_GEOMETRY_COMPLETE',len(cases),'instances,0newFE/decoder',flush=True)
    for case in cases:
        print(case['instance'],flush=True)
        for row in case['referenceGeometry']:
            if row['B']=='NSGA2_DEEP':print(row,flush=True)


if __name__=='__main__':main(Path(sys.argv[1]).resolve())

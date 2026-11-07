"""Paid-front-only optimistic half-budget pooling capacity; no search, decoder, selector or promotion."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
import numpy as np

from run_long_budget_bridge import ROOT, read, write_once, controller_lock, nondominated, hypervolume, igd_plus
from qpa_capability_analysis import endpoint, compare
from ctx_gom_capability_analysis import assessment
from research.semantic_repair.evidence import digest

SOURCE=ROOT/'runs/ctx-gom-capability-20261106-051509-678987'
HOMOGENEOUS=['SHARE_CTX_GOM','UNIFORM_CTX_GOM','NSGA_CTX_GOM','PA_JOINT','PA_EQUAL']


def capacity(root,plan):
    results=[]; seeds=plan['seeds']
    for spec in plan['instances']:
        stem,norm=spec['stem'],spec['normalization']
        full={(s,a):np.asarray(endpoint(SOURCE/stem/str(s)/('FE500K-'+a),'FE500K',500000)['front'],float)
              for s in seeds for a in plan['arms']}
        half={(s,a):np.asarray(endpoint(SOURCE/stem/str(s)/('FE500K-'+a),'FE500K',250000)['front'],float)
              for s in seeds for a in HOMOGENEOUS}
        reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in full.values()]))
        fronts=dict(full)
        for index,seed in enumerate(seeds):
            other=seeds[1-index]
            fronts[seed,'MIX_ORACLE']=nondominated(np.vstack([half[seed,'SHARE_CTX_GOM'],half[other,'UNIFORM_CTX_GOM']]))
            for arm in HOMOGENEOUS:
                fronts[seed,'RESTART_'+arm]=nondominated(np.vstack([half[seed,arm],half[other,arm]]))
        values={}
        for key,front in fronts.items():
            normal=(front-norm['lower'])/norm['scale']
            values[key]=dict(HV={str(r):hypervolume(normal,(r,)*3) for r in (1.25,1.5,2.)},IGDplus=igd_plus(normal,reference))
        comparisons=[]
        opponents=HOMOGENEOUS+['NSGA2_DEEP','FULL_SHARED_DEEP','LI_RECON_DEEP']+['RESTART_'+a for a in HOMOGENEOUS]
        for arm in opponents:
            result=compare('MIX_ORACLE',arm,seeds,values,fronts)
            kind='improvement' if arm in ('RESTART_SHARE_CTX_GOM','RESTART_UNIFORM_CTX_GOM') else 'noninferiority'
            result['capacityAssessment']=assessment(result,kind); comparisons.append(result)
        results.append(dict(instance=stem,referenceSize=len(reference),comparisons=comparisons,
            pass_=all(c['capacityAssessment']['pass_'] for c in comparisons)))
    return dict(instances=results,pass_=all(i['pass_'] for i in results),
        decision='CAPACITY_ONLY_NEW_CAUSAL_PROTOCOL_REQUIRED' if all(i['pass_'] for i in results) else 'STOP_SIMPLE_HALF_BUDGET_ROLE_POOLING',
        newSearchFE=0,newDecoderCalls=0,actualAlgorithmImplemented=False,sameTimeTested=False,goalAchieved=False)


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        assert read(SOURCE/'status.json')['status']=='COMPLETE'
        assert read(SOURCE/'independent-final-audit.json')['passed']
        root=ROOT/'runs'/datetime.now().strftime('ctx-gom-complement-capacity-%Y%m%d-%H%M%S-%f');root.mkdir()
        plan=read(SOURCE/'protocol.json')
        write_once(root/'protocol.json',dict(version='CTX_GOM_HALF_BUDGET_CAPACITY-v1',source=str(SOURCE),
            sourceAnalysisSHA256=digest(SOURCE/'analysis.json'),seeds=plan['seeds'],instances=[s['stem'] for s in plan['instances']],
            hypothesis='Observed extreme-HV versus interior-IGD/C tradeoff may contain enough complementary paid schedules to cover fullmethod gaps; test only optimistic capacity before implementing communication/allocation',
            registeredBeforeThisCalculation=True,developmentPosthocHypothesis=True,sourceFEPerStream=250000,totalFEEveryPool=500000,
            primary='Two preregistered crossseed SHARE250k+UNIFORM250k pools; no same-seed/ratio/endpoint scan or quality selection',
            controls='All five full500k versions plus frozen strongNSGA/oldsharing/Li; same-source250k+250k independentseed restart unions for each of five versions',
            reference='Exactly the original per-instance all10arms/all2seeds full500k NDunion and frozen scales/references; does not alter original qualification',
            criterion='Bothinstances: vsS/S andU/U restart pools use original improvementRule (HV>=1%,IGD/Cnonworse plus tails); vsallotherfull/restart controls use original strong noninferiorityRule. Every required comparison must pass; no2of3vote',
            limitation='Optimistic free archive merge of already paid schedules only. Two pairings share sources and are not independent seeds; restart control duplicated across pairings. No search feedback, running-time or communication benefit claim',
            onFailure='Do not implement simple halfbudget switch/restart/pooling or tune proportions; fixedfullalgorithm and prior stopped mechanisms remain stopped',
            newSearchFE=0,newDecoderCalls=0,defaultMainlineChanged=False,goalAchieved=False))
        (root/'source-script.py').write_text(open(__file__,encoding='utf-8').read(),encoding='utf-8')
        result=capacity(root,plan);write_once(root/'analysis.json',result)
        print('CTX_COMPLEMENT_CAPACITY_ROOT',root,flush=True);print('CTX_COMPLEMENT_CAPACITY_DECISION',result['decision'],flush=True)


if __name__=='__main__':main()

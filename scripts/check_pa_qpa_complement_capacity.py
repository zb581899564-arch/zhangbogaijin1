"""Fixed cross-kernel half-budget capacity, using saved paid fronts only."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import time
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock,nondominated,hypervolume,igd_plus
from qpa_capability_analysis import endpoint,compare
from ctx_gom_capability_analysis import assessment
from run_qpa_complete_engineering import protected
from research.semantic_repair.evidence import digest

SOURCE=ROOT/'runs/qpa-capability-pilot-20261106-025546-344483'
PARENTS=('PA_JOINT','QPA_DIRECT');RESTARTS=(*PARENTS,'PA_EQUAL')


def registered(root,plan):
    write_once(root/'protocol.json',dict(version='PA_QPA_FIXED_HALF_BUDGET_CAPACITY-v1',registeredBeforeCalculation=True,
        source=str(SOURCE),sourceAnalysisSHA256=digest(SOURCE/'fe500k-analysis.json'),sourceAuditSHA256=digest(SOURCE/'post-audit.json'),
        instances=[p['stem'] for p in plan['instances']],seeds=plan['seeds'],parentKernels=PARENTS,
        basis='Source report: QPA_DIRECT beats PA_JOINT on20, PA_JOINT beatsQPA on100; representation/program differences may provide complementary regions. This is untested capacity, not four-role novelty.',
        distinctFromPriorStop='Old half-budget source was SHARE_CTX_GOM versusUNIFORM_CTX_GOM, two preference variants of one PA-local framework. Here two standalone ordinary complete representations/programs are pooled; no source-role claim.',
        totalSourceFEEveryUnion=500000,sourceFEEveryStream=250000,
        primary='PA_JOINT seed_i250k +QPA_DIRECT seed_other250k, both fixed reciprocal pairings; no same-seed,ratio,checkpoint,instance-dependent or source selection',
        controls='Allsix full500k source methods; same-kernel two-seed250k+250k restart unions forPA_JOINT,QPA_DIRECT,PA_EQUAL',
        reference='Original allsixarms/alltwoseeds full500k empiricalND union, original frozen scales, HV1.25/1.5/2',
        criterion='Bothinstances: original improvementRule vs both parent same-kernel restart unions (medianHV>=1%, IGD+/Cnonworse, original per-seed floors); original noninferiorityRule vs all other full500k/restart controls. Allconditions required, no2of3 voting.',
        optimism='Free final archive merge, source initializations fully counted twice; merge/communication/time ignored makes this an optimistic capacity test. Not an executable algorithm, time claim, causal transfer evidence or independent confirmation.',
        dependence='Two reciprocal mixtures share allfour source trajectories; homogeneous restart pools identical across pairings. Report correlated development cases, not independent repetitions.',
        onFailure='Stop this fixed independent halfbudget PA/QPA pooling; no ratio,switch point,instance-dependent choice,source change or promotingPA_EQUAL after results. Does not stop all possible interaction architectures.',
        progression='Capacitypass only permits separatelyregistered interleaved interaction test with common-kernel ordinary control, role and sharing ablations; not four-role benefit or algorithmqualification',
        newSearchFE=0,newDecoderCalls=0,defaultMainlineChanged=False,goalAchieved=False,protectedBefore=protected()))


def instance(root,spec,plan):
    stem,norm=spec['stem'],spec['normalization'];seeds=plan['seeds'];fronts={};receipts={};identities={}
    for seed in seeds:
        initial=None
        for arm in plan['arms']:
            folder=SOURCE/stem/str(seed)/('FE500K-'+arm);receipt,=rows(folder/'run-receipt.jsonl')
            assert receipt['attempted']==receipt['successful']==receipt['decoder']['dynamic.evaluations']==500000 and receipt['failed']==0
            current=rows(folder/'initial-population.jsonl');assert len(current)==100
            if initial is None:initial=current
            assert current==initial
            fronts[seed,arm]=np.asarray(endpoint(folder,'FE500K',500000)['front']);receipts[seed,arm]=receipt
            identities[str(folder)]={n:digest(folder/n) for n in ('anytime.jsonl','initial-population.jsonl','run-receipt.jsonl')}
    half={(s,a):np.asarray(endpoint(SOURCE/stem/str(s)/('FE500K-'+a),'FE500K',250000)['front']) for s in seeds for a in RESTARTS}
    full_reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    for index,seed in enumerate(seeds):
        other=seeds[1-index]
        fronts[seed,'MIX_ORACLE']=nondominated(np.vstack([half[seed,'PA_JOINT'],half[other,'QPA_DIRECT']]))
        for arm in RESTARTS:fronts[seed,'RESTART_'+arm]=nondominated(np.vstack([half[seed,arm],half[other,arm]]))
    values={}
    for key,p in fronts.items():
        normal=(p-norm['lower'])/norm['scale']
        values[key]=dict(HV={str(r):hypervolume(normal,(r,)*3) for r in (1.25,1.5,2.)},IGDplus=igd_plus(normal,full_reference))
    comparisons=[]
    for opponent in [*plan['arms'],*['RESTART_'+a for a in RESTARTS]]:
        row=compare('MIX_ORACLE',opponent,seeds,values,fronts)
        row['capacityAssessment']=assessment(row,'improvement' if opponent in ('RESTART_PA_JOINT','RESTART_QPA_DIRECT') else 'noninferiority')
        comparisons.append(row)
    observations=[dict(seed=s,arm=a,front=p.tolist(),metrics=values[s,a]) for (s,a),p in fronts.items()]
    write_once(root/(stem+'-source-identities.json'),identities)
    return dict(instance=stem,normalization=norm,reference=full_reference.tolist(),observations=observations,comparisons=comparisons,
        pass_=all(r['capacityAssessment']['pass_'] for r in comparisons))


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        started=time.perf_counter();assert read(SOURCE/'status.json')['status']=='COMPLETE' and read(SOURCE/'post-audit.json')['passed']
        plan=read(SOURCE/'protocol.json');root=ROOT/'runs'/datetime.now().strftime('pa-qpa-complement-capacity-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PA_QPA_CAPACITY_ROOT',root,flush=True);registered(root,plan);shutil.copy2(Path(__file__),root/'source-script.py')
        results=[instance(root,spec,plan) for spec in plan['instances']];passed=all(r['pass_'] for r in results)
        assert protected()==read(root/'protocol.json')['protectedBefore']
        result=dict(instances=results,pass_=passed,decision='CAPACITY_ONLY_SEPARATE_INTERACTION_PROTOCOL_REQUIRED' if passed else 'STOP_FIXED_INDEPENDENT_PA_QPA_HALF_BUDGET_POOLING',
            newSearchFE=0,newDecoderCalls=0,wallSeconds=time.perf_counter()-started,algorithmImplemented=False,sameTimeTested=False,
            fourRoleIndependentBenefitTested=False,defaultMainlineChanged=False,goalAchieved=False)
        write_once(root/'analysis.json',result);print('PA_QPA_CAPACITY_COMPLETE',result['decision'],flush=True)
        for item in results:
            print(item['instance'],[(r['B'],r['medianHVEffectPct']['1.5'],r['medianIGDplusSymmetricWorseningPct'],r['capacityAssessment']['pass_']) for r in item['comparisons']],flush=True)


if __name__=='__main__':main()

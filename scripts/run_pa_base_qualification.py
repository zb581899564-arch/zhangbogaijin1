"""One independent ordinary-baseline qualification, unchanged methods; never reopens failed learning claim."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,write_once,controller_lock
from pa_capability_support import ARMS,SOURCE,run_case,initial_key,fees
from pa_capability_analysis import analyze
from research.semantic_repair.evidence import digest

PILOT=ROOT/'runs/pa-capability-pilot-20261105-175700-160861'
INTERFACE=ROOT/'runs/pa-capability-interfaces-20261105-175043-036508'


def readiness(result):
    checked=[]
    for instance in result['instances']:
        comparisons={r['control']:r for r in instance['comparisons']};controls={}
        for name in ('NSGA2_PLAIN','NSGA2_DEEP','FULL_SHARED_DEEP','LI_RECON_DEEP'):
            row=comparisons[name]
            controls[name]=bool(row['medianHVEffectPct']['1.5']>=1-1e-10 and row['nonnegativeEverySeed']
                and row['referenceDirectionStable'] and row['auxiliaryPass'])
        checked.append({'stem':instance['stem'],'controlPass':controls,'pass':all(controls.values())})
    return {'phase':result['phase'],'instances':checked,'pass':all(r['pass'] for r in checked),
            'learningClaimReopened':False,'scope':'Ordinary unchanged search-base qualification only, not proposed innovation'}


def phase(root,cp,plan,kind,completed):
    for s,spec in enumerate(plan['instances']):
        for k,seed in enumerate(plan['seeds']):
            shift=(s+k)%len(ARMS);order=ARMS[shift:]+ARMS[:shift];expected=None
            for arm in order:
                seconds=spec['time_seconds'] if kind=='TIME' else float('inf')
                limit=plan['timeSafetyFE'] if kind=='TIME' else plan['fe500k'];stem=spec['stem']
                out,receipt=run_case(root,cp,stem,arm,f'{seed}/{kind}-{arm}',limit,seed,seconds);completed.append((out,receipt))
                key=initial_key(out);assert len(key)==100
                if expected is None:expected=key
                else:assert key==expected
                if kind=='TIME':assert key==initial_key(root/stem/str(seed)/('FE500K-'+order[0]))
    result=analyze(root,kind);gate=readiness(result);write_once(root/(kind.lower()+'-readiness.json'),gate)
    print('PA_BASE_READINESS',kind,gate['pass'],flush=True);return result,gate


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        assert read(PILOT/'analysis.json')['decision']=='STOP_FIXED_PA_MO_GLOBAL_ADAPTATION'
        root=ROOT/'runs'/datetime.now().strftime('pa-base-qualification-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PA_BASE_QUALIFICATION_ROOT',root,flush=True);completed=[]
        old=read(PILOT/'protocol.json')
        shared_keys=('instances','arms','fe100k','fe500k','timeSafetyFE','timeStage','numericTolerance','IGDplus',
                     'initialization','jointAndRelabel','controls','noLocalPA','limits')
        plan={**{key:old[key] for key in shared_keys},'version':'ORDINARY_PA_BASE_QUALIFICATION-v1','seeds':[13910003,13910037],
            'previousStoppedPilot':str(PILOT),'previousFailure':'Learning advantage failed; its stopped decision and skipped stages are permanent',
            'newQuestion':'Can the SAME previously designated primary ordinary method serve as a competitive500k/true-time search base for later four-role/shared research, without claiming learned linkage novelty?',
            'registeredAfterExploratoryPilot':True,'algorithmOrParametersChanged':False,'primaryStill':'PA_JOINT, not posthoc best ofJOINT/RELABEL',
            'plannedFixedSuccessfulFE':12000000,'phases':['FE500K','TIME ifFE500Kreadinesspasses'],
            'readinessGate':'BOTHinstances vsEACHofNSGA2_PLAIN/NSGA2_DEEP/FULL_SHARED_DEEP/LI_RECON_DEEP: medianHV>=1%,bothfreshseed effects>=0,ref1.25/2median>=0,median symmetricIGD+worsening<=5%',
            'learningGateNotUsed':'This qualifies an ordinary baseline, not a new learned method; failed learning claim cannot be restored even if these diagnostics become positive',
            'oneFollowupOnly':'No more seeds,horizons,operator/model/role/population changes or selectingRELABELifprimaryfails. Failure ends this unchanged-base qualification',
            'qualificationLimit':'Passing allows a separate four-role/shared independent-gain protocol. It does not qualify a finalinnovative algorithm or completegoal',
            'defaultMainlineChanged':False,'goalAchieved':False}
        write_once(root/'protocol.json',plan)
        cp=(INTERFACE/'classpath.txt').read_text('utf-8-sig').strip();(root/'classpath.txt').write_text(cp,encoding='utf-8')
        for name in ('run_pa_base_qualification.py','pa_capability_analysis.py','pa_capability_support.py'):
            shutil.copy2(Path(__file__).with_name(name),root/name)
        write_once(root/'controller-hashes.json',{p.name:digest(p) for p in root.glob('*.py')})
        try:
            for spec in plan['instances']:shutil.copytree(SOURCE/spec['stem']/'inputs',root/spec['stem']/'inputs')
            fe,gate=phase(root,cp,plan,'FE500K',completed);results=[fe];gates=[gate]
            if gate['pass']:
                timed,time_gate=phase(root,cp,plan,'TIME',completed);results.append(timed);gates.append(time_gate)
            passed=all(r['pass'] for r in gates) and len(gates)==2
            decision='QUALIFIED_ORDINARY_SEARCH_BASE_ONLY' if passed else 'ORDINARY_BASE_NOT_QUALIFIED_STOP'
            write_once(root/'analysis.json',{'phases':results,'readiness':gates,'decision':decision,**fees(completed),
                'learningClaimStillUnsupported':True,'finalResearchAlgorithmProved':False,'goalAchieved':False})
        except BaseException as error:
            write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','error':repr(error),'completedRuns':len(completed),**fees(completed)});raise
        write_once(root/'status.json',{'status':'COMPLETE','runs':len(completed),'decision':decision,**fees(completed),'goalAchieved':False})
        print('PA_BASE_QUALIFICATION_COMPLETE',decision,fees(completed),flush=True)


if __name__=='__main__':main()

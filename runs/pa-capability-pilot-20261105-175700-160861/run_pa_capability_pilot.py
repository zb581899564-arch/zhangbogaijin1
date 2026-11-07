"""Frozen6arm fresh-seed complete-method pilot, gated real time and500k follow-up, no default changes."""
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

INTERFACE=ROOT/'runs/pa-capability-interfaces-20261105-175043-036508'
SEEDS=(13810003,13810037)


def phase(root,cp,plan,label,completed):
    initial={}
    for s,spec in enumerate(plan['instances']):
        stem=spec['stem']
        for k,seed in enumerate(SEEDS):
            shift=(s+k)%len(ARMS);order=ARMS[shift:]+ARMS[:shift]
            for arm in order:
                limit=plan['timeSafetyFE'] if label=='TIME' else plan['fe100k'] if label=='FE100K' else plan['fe500k']
                seconds=spec['time_seconds'] if label=='TIME' else float('inf')
                name=f'{seed}/{label}-{arm}'
                out,receipt=run_case(root,cp,stem,arm,name,limit,seed,seconds);completed.append((out,receipt))
                key=initial_key(out);assert len(key)==100
                expected=initial.setdefault((stem,seed),key);assert key==expected,'Scientific initial vectors differ'
                # Match every budget phase to the first arm of its same fresh-seed FE phase too.
                if label!='FE100K':
                    reference=root/stem/str(seed)/('FE100K-'+ARMS[(s+k)%len(ARMS)])
                    assert key==initial_key(reference)
    return analyze(root,label)


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        assert read(INTERFACE/'status.json')['interfacePass']
        root=ROOT/'runs'/datetime.now().strftime('pa-capability-pilot-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PA_CAPABILITY_PILOT_ROOT',root,flush=True);completed=[];results=[]
        plan={'version':'PA_MO_CAPABILITY_PILOT-v1','interfaceSource':str(INTERFACE),
            'instances':read(ROOT/'runs/makespan-tie-screen-20261105-025223-471920/protocol.json')['instances'],
            'seeds':SEEDS,'arms':ARMS,'fe100k':100000,'fe500k':500000,'timeSafetyFE':5000000,
            'plannedFE100kSuccessful':2400000,'plannedAdditionalFE500kSuccessfulIfAllStrongGatesPass':12000000,
            'timeStage':'Actual4/5s,0.5T/Tcheckpoints, all constructors/initialization/model/archive/capture inside common clock; post-search QA separate',
            'gateSequence':'FE100K -> TIME only if learning and ordinary-global gates both pass. FE500K only if FE100K and TIME both pass all strong controls. Never extend failed seeds/budgets',
            'learningGate':'BOTHinstances: medianHV_JOINTvsRELABEL>=1%, BOTHseed effects>=0, ref1.25/2median direction>=0',
            'ordinaryGlobalGate':'BOTHinstances: medianHV_JOINTvsNSGA2_PLAIN>=0 and median symmetricIGD+worsening<=5%',
            'strongControlGate':'BOTHinstances vsEACHofNSGA2_DEEP/FULL_SHARED_DEEP/LI_RECON_DEEP: medianHV>=1%,bothseed effects>=0,ref1.25/2median>=0,median symmetricIGD+worsening<=5%',
            'numericTolerance':'HV direction/1% comparison tolerance1e-10percentagepoints only; no practical threshold relaxation',
            'IGDplus':'Common ND union across all6arms andbothseeds, separately byinstance/budget, normalized by frozen scales. Symmetric worsening200*(A-B)/(A+B),0ifboth0; never feeds search',
            'initialization':'Actual common100fourvectors andobjectives must match EVERYarm andphase perinstance/seed. PA initial stable creationorder slots15M/55CENTER/15E/15W, no objective sorting or regrouping',
            'jointAndRelabel':'Published fixed weight2/3, all2N-1subsets includingroot, samefull lifecycle; RELABEL preserves own learned tree shape/cost, separate per-generation RNG seed=algorithmSeed xor0x51a7c3 then xor0x9e3779b97f4a7c15*generation',
            'controls':'Separate plain NSGA class, original selection/variation/initialization, only deep block removed. Strong class byte-unchanged; FULL/LI reuse exact frozen properties and naturaldeepLS',
            'noLocalPA':'Both PA methods have no local search/shared selector/QGS. Losing to enhanced method is an absolute gap, not isolated evidence against all joint modeling',
            'conditionalLSBranch':'Only if capability gates pass FEandTIME butstrong gate fails: permitone separately frozen matchedordinarydeepLS protocol forPAandcontrols. No depths/order/quota scan',
            'failure':'Retain logs,lastfront,fees,no seedreplacement. Identifiability/engineering failures never counted as algorithm failure',
            'stop':'Failed learning/global capability stops this fixedPA-MOglobaladaptation. No changingpopulation,roles,weights,root,donors,acceptance,tree/model/seed/window to rescue',
            'limits':'Repeateddevelopment instances, freshalgorithmseeds only. Ordinary joint method is notourinnovation orfinalresearchalgorithm; fourroles/shared independent value andmultiinstanceconfirmation still required',
            'defaultMainlineChanged':False,'externalTransfers':False,'goalAchieved':False}
        write_once(root/'protocol.json',plan)
        cp=(INTERFACE/'classpath.txt').read_text('utf-8-sig').strip();(root/'classpath.txt').write_text(cp,encoding='utf-8')
        for name in ('run_pa_capability_pilot.py','pa_capability_analysis.py','pa_capability_support.py'):
            shutil.copy2(Path(__file__).with_name(name),root/name)
        write_once(root/'controller-hashes.json',{p.name:digest(p) for p in root.glob('*.py')})
        try:
            for spec in plan['instances']:
                shutil.copytree(SOURCE/spec['stem']/'inputs',root/spec['stem']/'inputs')
            fe=phase(root,cp,plan,'FE100K',completed);results.append(fe)
            print('PA_CAPABILITY_FE_GATE',fe['learningGate'],fe['ordinaryGlobalGate'],fe['strongControlGate'],flush=True)
            if not fe['capabilityGate']:
                decision='STOP_FIXED_PA_MO_GLOBAL_ADAPTATION';skipped=['TIME','FE500K']
            else:
                timed=phase(root,cp,plan,'TIME',completed);results.append(timed)
                if not timed['capabilityGate']:
                    decision='STOP_FIXED_PA_MO_GLOBAL_ADAPTATION';skipped=['FE500K']
                elif not(fe['strongControlGate'] and timed['strongControlGate']):
                    decision='ALLOW_ONE_SEPARATE_MATCHED_LS_PROTOCOL';skipped=['FE500K']
                else:
                    long=phase(root,cp,plan,'FE500K',completed);results.append(long);skipped=[]
                    decision='DESIGN_FOUR_ROLE_AND_SHARING_INTEGRATION' if long['capabilityGate'] and long['strongControlGate'] else 'STOP_FIXED_PA_MO_GLOBAL_ADAPTATION'
            write_once(root/'analysis.json',{'phases':results,'decision':decision,'skippedPhases':skipped,**fees(completed),
                'newDefaultAlgorithmPromoted':False,'goalAchieved':False})
        except BaseException as error:
            write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','error':repr(error),'completedRuns':len(completed),**fees(completed)});raise
        write_once(root/'status.json',{'status':'COMPLETE','runs':len(completed),'decision':decision,**fees(completed),'goalAchieved':False})
        print('PA_CAPABILITY_PILOT_COMPLETE',decision,fees(completed),flush=True)


if __name__=='__main__':main()

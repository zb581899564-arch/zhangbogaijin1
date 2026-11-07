"""Fixed199760-FE isolated engineering after a zero-decoder math precondition."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from run_pa_role_schedule_engineering import first_model
from pa_regional_engineering_build import build
from pa_regional_engineering_support import totals,run_one,source_command

CONTRACT=ROOT/'research/gomea_reference_audit/PA_CENTER_REGIONAL_ENGINEERING_V1.json'


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();root=ROOT/'runs'/datetime.now().strftime('pa-center-regional-engineering-%Y%m%d-%H%M%S-%f')
        root.mkdir();print('PA_CENTER_REGIONAL_ENGINEERING_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        try:
            cp=build(root,plan);checks=[]
            opportunity=read(Path(plan['opportunityRoot'])/'protocol.json')['contract'];scales={s['instance']:s['scale'] for s in opportunity['cases']}
            for spec in plan['cases']:
                stem=spec['instance'];inputs=root/stem/'inputs';inputs.mkdir(parents=True);command,at=source_command(spec)
                for offset,name in enumerate((stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt','sources.tsv'),1):shutil.copy2(Path(command[at+offset]),inputs/name)
                assert digest(inputs/'sources.tsv')==digest(Path(spec['initialSourceTSV']))
                write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in inputs.iterdir()})
                native=None;masters={}
                for mode in plan['modes']:
                    folder,receipt,proof=run_one(root,cp,plan,spec,mode,mode,spec['masterFE'],scales[stem])
                    assert receipt['completedGenerations']==2 and receipt['completedPrograms']==200;model=first_model(folder)
                    if mode=='OFF':
                        native=model;old,=rows(Path(spec['source'])/'receipt.jsonl')
                        assert receipt['paidSHA256']==old['paidSHA256'] and receipt['lastValidFront']==old['lastValidFront']
                    else:assert model==native
                    masters[mode]=proof;checks.append(dict(instance=stem,mode=mode,firstModelOrFullNativeParity=True,allPaidPhysicsAndTracePassed=True))
                for mode in ('REGIONAL','NO_SPECIALIST'):
                    for limit in spec['cutoffs']:
                        _,receipt,_=run_one(root,cp,plan,spec,mode,mode+'-cut'+str(limit),limit,scales[stem])
                        assert receipt['paidSHA256']==masters[mode]['prefixSHA256'][str(limit)]
            actual=totals(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedActualAttemptedFE']
            assert actual['failedFE']==0 and actual['runs']==plan['expectedRuns'] and protected()==before
            write_once(root/'acceptance.json',dict(passed=True,checks=checks,**actual,newPerformanceEvidence=False,defaultMainlineChanged=False,goalAchieved=False))
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**totals(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',engineeringPass=True,**actual,goalAchieved=False))
        print('PA_CENTER_REGIONAL_ENGINEERING_PASS',actual,flush=True)


if __name__=='__main__':main()

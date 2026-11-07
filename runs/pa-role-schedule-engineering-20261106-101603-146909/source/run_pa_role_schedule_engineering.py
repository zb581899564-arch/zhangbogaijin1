"""Full role/visit factor engineering:311646 fixedFE, no performance inference."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
from datetime import datetime
import json
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from pa_role_engineering_support import build,run_one,receipts

CONTRACT=ROOT/'research/gomea_reference_audit/PA_ROLE_SCHEDULE_ENGINEERING_V1.json'


def first_model(folder):
    states={}
    with (folder/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line)
            if event['kind'] in ('initial','reencode'):states[event['id']]=event
            if event['kind']=='model':
                return dict(population=[{k:states[p['id']][k] for k in ('id','paidFE','hash','objectives','resources','keys')} for p in event['population']],
                    dependency=event['dependency'],subsets=event['subsets'])
    raise AssertionError('No model')


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();root=ROOT/'runs'/datetime.now().strftime('pa-role-schedule-engineering-%Y%m%d-%H%M%S-%f')
        root.mkdir();print('PA_ROLE_SCHEDULE_ENGINEERING_ROOT',root,flush=True)
        amendment=ROOT/'research/gomea_reference_audit/PA_ROLE_SCHEDULE_ENGINEERING_AMENDMENT_V1.json'
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before,
            engineeringAmendment=read(amendment) if amendment.exists() else None))
        try:
            cp=build(root,plan);checks=[]
            for spec in plan['cases']:
                stem=spec['stem'];source=Path(plan['sourceEngineering'])/stem/'main';command=read(source/'command.json');at=command.index('research.dynamic.PaPopulationRun')
                inputs=root/stem/'inputs';inputs.mkdir(parents=True)
                for offset,name in enumerate((stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt','sources.tsv'),1):shutil.copy2(Path(command[at+offset]),inputs/name)
                write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in inputs.iterdir()})
                native=None;master=None
                for mode in plan['modes']:
                    folder,receipt,analysis=run_one(root,cp,plan,spec,mode,mode,spec['masterFE'])
                    assert receipt['completedGenerations']==2 and receipt['completedPrograms']==200
                    model=first_model(folder)
                    if mode=='NATIVE':
                        native=model;old,=rows(source/'audit/receipt.jsonl')
                        assert receipt['paidSHA256']==old['paidSHA256'] and receipt['lastValidFront']==old['lastValidFront']
                    else:assert model==native
                    if mode=='FULL':master=analysis
                    checks.append(dict(instance=stem,mode=mode,nativeParityOrFirstModelEqual=True,fullStepAndPhysicalQA=True))
                for limit in spec['cutoffs']:
                    _,receipt,result=run_one(root,cp,plan,spec,'FULL','cut'+str(limit),limit)
                    assert receipt['paidSHA256']==master['prefixSHA256'][str(limit)]
            actual=receipts(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedFixedFE'] and actual['failedFE']==0 and actual['runs']==24
            assert protected()==before
            write_once(root/'acceptance.json',dict(passed=True,checks=checks,**actual,newPerformanceEvidence=False,defaultMainlineChanged=False,goalAchieved=False))
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**receipts(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',engineeringPass=True,**actual,goalAchieved=False));print('PA_ROLE_ENGINEERING_PASS',actual,flush=True)


if __name__=='__main__':main()

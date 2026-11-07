"""Prospective nine-arm new-seed pilot, no default change or failed-version tuning."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT,read,write_once,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from ctx_gom_capability_support import counts
from pa_capability_support import initial_key
from ctx_fork_pilot_support import build,bridge,run_one
from ctx_fork_pilot_analysis import analyze

CONTRACT=ROOT/'research/gomea_reference_audit/CTX_FIRST_LOCAL_FORK_PILOT_V1.json'


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();root=ROOT/'runs'/datetime.now().strftime('ctx-first-local-fork-pilot-%Y%m%d-%H%M%S-%f')
        root.mkdir();print('CTX_FIRST_LOCAL_FORK_PILOT_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        try:
            cp,base=build(root,plan)
            for spec in plan['instances']:
                stem=spec['stem'];shutil.copytree(Path(plan['source'])/stem/'inputs',root/stem/'inputs')
                write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in (root/stem/'inputs').iterdir()})
            bridge(root,cp,base,plan)
            for index,spec in enumerate(plan['instances']):
                for k,seed in enumerate(plan['seeds']):
                    shift=(index+k)%len(plan['arms']);order=plan['arms'][shift:]+plan['arms'][:shift];initial=None
                    for arm in order:
                        real,mode=plan['armDefinitions'][arm]
                        folder,_=run_one(root,cp,plan,spec,real,mode,seed,str(seed)+'/FE-'+arm,spec['fixedFE'])
                        current=initial_key(folder)
                        if initial is None:initial=current
                        assert len(current)==100 and current==initial
            actual=counts(root)
            assert actual['successfulFE']==actual['attemptedFE']==plan['plannedTotalAttemptedFE'] and actual['runs']==52
            assert actual['failedFE']==actual['timeInterruptedAttempts']==0
            assert protected()==before
            assert class_hashes(root/'classes')==read(root/'class-hashes.json')['wrapper']
            assert class_hashes(root/'kernel-classes')==read(root/'class-hashes.json')['kernel']
            result=analyze(root,plan,actual)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**counts(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],**actual,goalAchieved=False))
        print('CTX_FIRST_LOCAL_FORK_PILOT_COMPLETE',result['decision'],actual,flush=True)
        for item in result['instances']:
            for row in item['comparisons']:
                print(item['instance'],row['B'],row['medianHVEffectPct']['1.5'],row['medianIGDplusSymmetricWorseningPct'],row['medianC_A_B'],row['medianC_B_A'],row['registeredAssessment']['pass_'],flush=True)


if __name__=='__main__':main()

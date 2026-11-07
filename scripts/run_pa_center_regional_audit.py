"""Frozen zero-FE necessary-opportunity check; not a counterfactual optimization run."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import time

from run_long_budget_bridge import ROOT,read,write_once,controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from pa_center_regional_audit import analyze

CONTRACT=ROOT/'research/gomea_reference_audit/PA_CENTER_REGIONAL_AUDIT_V1.json'


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();root=ROOT/'runs'/datetime.now().strftime('pa-center-regional-audit-%Y%m%d-%H%M%S-%f')
        root.mkdir();print('PA_CENTER_REGIONAL_AUDIT_ROOT',root,flush=True);start=time.monotonic()
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before))
        source=root/'source';source.mkdir()
        for name in (Path(__file__).name,'pa_center_regional_audit.py'):shutil.copy2(Path(__file__).with_name(name),source)
        write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
        try:
            cases=[]
            for spec in plan['cases']:
                folder=Path(spec['source'])
                for name,sha in spec['sourceHashes'].items():assert digest(folder/name)==sha
                assert read(folder/'role-independent-replay.json')['passed']
                case=dict(instance=spec['instance'],**analyze(folder,spec['scale'],plan['thresholds']));cases.append(case)
                print('CENTER_REGIONAL_CASE',case['instance'],{m:{k:v for k,v in r.items() if k in ('acceptedWorseFraction','rejectedBetterFraction','pass_')} for m,r in case['modes'].items()},flush=True)
            assert protected()==before
            result=dict(cases=cases,pass_=all(c['pass_'] for c in cases),newSearchFE=0,newObjectiveQueries=0,newDecoderCalls=0,
                paidRowsRead=sum(c['paidRowsRead'] for c in cases),seconds=time.monotonic()-start,
                scope='Original native ordinary-PA trajectories only; fixed-direction hypothetical decision opportunities, not causal performance or proof explaining every FULL failure',
                decision='OPPORTUNITY_ONLY_SEPARATE_ENGINEERING_REQUIRED' if all(c['pass_'] for c in cases) else 'STOP_FIXED_REGIONAL_CENTER_OPPORTUNITY',
                previousStopsUnchanged=True,defaultMainlineChanged=False,goalAchieved=False)
            write_once(root/'analysis.json',result)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),newSearchFE=0,newDecoderCalls=0,goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],newSearchFE=0,newDecoderCalls=0,goalAchieved=False))
        print('PA_CENTER_REGIONAL_AUDIT_COMPLETE',result['decision'],result['paidRowsRead'],flush=True)


if __name__=='__main__':main()

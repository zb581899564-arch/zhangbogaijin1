"""Execute the registered ordinary donor-feedback pilot; defaults and prior stops remain frozen."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from run_qpa_complete_engineering import protected
from ctx_gom_capability_support import counts
from pa_capability_support import initial_key
from qpa_capability_analysis import endpoint
from qpa_feedback_pilot_support import build,prepare_inputs,run_one
from qpa_feedback_pilot_analysis import analyze
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

CONTRACT=ROOT/'research/gomea_reference_audit/QPA_COMPLETED_DONOR_PILOT_V1.json'


def bridge(root,paths,plan):
    evidence=[];source=Path(plan['sourceQpa'])
    for spec in plan['instances']:
        stem=spec['stem'];old=source/stem/'ENGINE-LIGHT';receipt,=rows(old/'run-receipt.jsonl');limit=receipt['successful']
        out,new=run_one(root,paths,plan,stem,'SYNC','BRIDGE-SYNC',14670003,limit,bridge=True)
        assert new['paidSHA256']==receipt['paidSHA256'] and new['search']['completeGenerations']==2
        assert endpoint(out,'FE',limit)['front']==endpoint(old,'FE',limit)['front'] and initial_key(out)==initial_key(old)
        evidence.append(dict(instance=stem,successfulFE=limit,wholePaidSHA256=new['paidSHA256'],wholeTwoGenerationLightParity=True))
    actual=counts(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedBridgeFE']<=plan['maximumBridgeAttemptedFE']
    write_once(root/'bridge-acceptance.json',dict(passed=True,instances=evidence,**actual))


def scientific(root,paths,plan):
    for index,spec in enumerate(plan['instances']):
        for seed_index,seed in enumerate(plan['seeds']):
            shift=(index+seed_index)%len(plan['arms']);order=plan['arms'][shift:]+plan['arms'][:shift];expected=None
            for arm in order:
                folder,_=run_one(root,paths,plan,spec['stem'],arm,f'{seed}/FE100K-{arm}',seed,plan['fixedFE'])
                initial=initial_key(folder);assert len(initial)==100
                if expected is None:expected=initial
                else:assert initial==expected
            print('QPA_FEEDBACK_NINE_ARM_CONTEXT_COMPLETE',spec['stem'],seed,flush=True)


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);before=protected();extra=digest(ROOT/'src/algorithms/model_global/qpa/QpaPopulation.java')
        root=ROOT/'runs'/datetime.now().strftime('qpa-completed-donor-pilot-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('QPA_FEEDBACK_PILOT_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before,originalQpaPopulationSHA256=extra))
        try:
            paths=build(root,plan);prepare_inputs(root,plan);bridge(root,paths,plan);scientific(root,paths,plan)
            actual=counts(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedBridgeFE']+plan['plannedScientificFE']<=plan['maximumTotalAttemptedFE']
            assert actual['failedFE']==actual['timeInterruptedAttempts']==0 and actual['runs']==38
            assert protected()==before and digest(ROOT/'src/algorithms/model_global/qpa/QpaPopulation.java')==extra
            for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
            assert class_hashes(root/'kernel-classes')==read(root/'class-hashes.json')['kernel']
            assert class_hashes(root/'classes')==read(root/'class-hashes.json')['wrapper']
            result=analyze(root,plan,actual)
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**counts(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',decision=result['decision'],**actual,goalAchieved=False))
        print('QPA_FEEDBACK_PILOT_COMPLETE',result['decision'],actual,flush=True)


if __name__=='__main__':main()

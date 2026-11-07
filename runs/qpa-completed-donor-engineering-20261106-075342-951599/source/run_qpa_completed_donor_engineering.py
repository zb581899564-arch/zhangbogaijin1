"""Prospective ordinary lifecycle engineering only; no performance acceptance or mainline edit."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import gc
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from run_qpa_complete_engineering import protected,fees
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from qpa_feedback_engineering import build,run_one,replay,trajectory

CONTRACT=ROOT/'research/gomea_reference_audit/QPA_COMPLETED_DONOR_ENGINEERING_V1.json'


def instance(root,cp,source,spec):
    stem=spec['stem'];shutil.copytree(source/stem/'inputs',root/stem/'inputs')
    write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in (root/stem/'inputs').iterdir()})
    native_receipt,=rows(source/stem/'main/receipt.jsonl')
    sync=run_one(root,cp,spec,'SYNC','SYNC',spec['syncTwoGenerationFE'],2);sync_receipt,=rows(sync/'receipt.jsonl')
    assert sync_receipt['paidSHA256']==native_receipt['paidSHA256'] and sync_receipt['lastValidFront']==native_receipt['lastValidFront']
    assert sync_receipt['successfulFE']==native_receipt['successfulFE']
    native=trajectory(source/stem/'main');sync_trace=trajectory(sync);assert native==sync_trace
    write_once(sync/'native-full-parity.json',dict(passed=True,successfulFE=sync_receipt['successfulFE'],wholePaidSHA256=sync_receipt['paidSHA256'],
        fullRawPaidSequenceAndFirstGenerationDrawsEqual=True,completeGenerations=sync_receipt['completedGenerations']))
    records={};initial=rows(sync/'initial-population.jsonl')
    for mode in ('OWN','ALL'):
        folder=run_one(root,cp,spec,mode,mode,spec['firstGenerationFE'],1)
        proof=replay(folder,mode,spec['cuts']);write_once(folder/'independent-replay.json',proof);gc.collect()
        trace=trajectory(folder);assert trace['drawSHA256']==sync_trace['drawSHA256'] and trace['activeSubsets']==sync_trace['activeSubsets']
        assert rows(folder/'initial-population.jsonl')==initial
        assert proof['completeGenerations']==1 and proof['completePrograms']==100 and proof['paidReconstructed']==spec['firstGenerationFE']
        assert trace['firstFreshFE'] is not None
        assert trace['raw'][:trace['firstFreshFE']-1]==sync_trace['raw'][:trace['firstFreshFE']-1]
        records[mode]=dict(proof=proof,firstFreshFE=trace['firstFreshFE'],commonFirstGenerationDrawSHA256=trace['drawSHA256'])
        if mode=='OWN':assert proof['crossRoleFreshMaskReads']==0
        else:assert proof['crossRoleFreshMaskReads']>0
    cuts=[]
    for cutoff in spec['cuts']:
        folder=run_one(root,cp,spec,'ALL','ALL-cut'+str(cutoff),cutoff,-1)
        proof=replay(folder,'ALL',[]);write_once(folder/'independent-replay.json',proof);gc.collect()
        assert proof['paidSHA256']==records['ALL']['proof']['prefixSHA256'][str(cutoff)]
        cuts.append(dict(cutoff=cutoff,paidPrefixEqual=True,lastPhase=rows(folder/'receipt.jsonl')[0]['phase']))
    result=dict(instance=stem,syncWholeTwoGenerationsNativeEqual=True,initial100AndFirstGenerationDrawsEqual=True,
        completedDonorRulesAndPaidStateReconstruction=True,records=records,cutoffs=cuts)
    write_once(root/stem/'acceptance.json',result);return result


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan=read(CONTRACT);source=Path(plan['source']);visibility=Path(plan['visibilityEvidence'])
        assert read(visibility/'analysis.json')['necessaryCoveragePass'] and digest(visibility/'analysis.json')==plan['visibilityAnalysisSHA256']
        root=ROOT/'runs'/datetime.now().strftime('qpa-completed-donor-engineering-%Y%m%d-%H%M%S-%f');root.mkdir();before=protected()
        extra_protected=digest(ROOT/'src/algorithms/model_global/qpa/QpaPopulation.java')
        print('QPA_FEEDBACK_ENGINEERING_ROOT',root,flush=True)
        write_once(root/'protocol.json',dict(contract=plan,contractSHA256=digest(CONTRACT),protectedBefore=before,originalQpaPopulationSHA256=extra_protected))
        try:
            cp=build(root,source);results=[instance(root,cp,source,spec) for spec in plan['instances']];actual=fees(root)
            assert actual['successfulFE']==actual['attemptedFE']==plan['plannedActualSearchFE']<=plan['maximumActualAttemptedSearchFE'] and actual['failedFE']==0
            assert actual['paidFullTimelineQA']==actual['successfulFE'] and actual['receiptCount']==12
            assert protected()==before and digest(ROOT/'src/algorithms/model_global/qpa/QpaPopulation.java')==extra_protected
            assert class_hashes(root/'classes')==read(root/'class-hashes.json')
            for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
            write_once(root/'analysis.json',dict(engineeringPass=True,instances=results,**actual,performanceProved=False,
                donorFeedbackFourRoleContributionProved=False,defaultMainlineChanged=False,goalAchieved=False))
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**fees(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',engineeringPass=True,**actual,goalAchieved=False))
        print('QPA_FEEDBACK_ENGINEERING_COMPLETE',actual,flush=True)


if __name__=='__main__':main()

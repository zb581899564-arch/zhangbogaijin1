"""Two fixed complete500k paired observer replays; two million diagnostic FE, no new performance variant."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from ctx_pipeline_build import SOURCE,build
from ctx_gom_capability_support import checked
from run_snapshot_anchor_audit import override
from research.semantic_repair.evidence import digest
from frozen_classpath_identity import verify_capture
from run_qpa_complete_engineering import protected
from pa_capability_support import initial_key

STEM='100_2_3_1';SEED=14910003;ARMS=('SHARE_CTX_GOM','UNIFORM_CTX_GOM')


def fees(root):
    rs=[rows(p)[0] for p in root.glob('*/*/run-receipt.jsonl')]
    return dict(runs=len(rs),attemptedFE=sum(r['attempted'] for r in rs),successfulFE=sum(r['successful'] for r in rs),failedFE=sum(r['failed'] for r in rs),
        offlineCheckpointQA=sum(read(p.parent/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p in root.glob('*/*/run-receipt.jsonl') if (p.parent/'checkpoint-validation.json').exists()))


def run_one(root,cp,arm,observed):
    label=arm+('-OBSERVED' if observed else '-FROZEN');out=root/STEM/label;out.mkdir()
    old=SOURCE/STEM/str(SEED)/('FE500K-'+arm);cmd=read(old/'command.json');entry=cmd.index('research.dynamic.GomCapabilityRun')
    cmd[cmd.index('-cp')+1]=cp;cmd[entry+4]=str(out)
    for j,name in enumerate((STEM+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),entry+1):cmd[j]=str(root/STEM/'inputs'/name)
    cmd=override(cmd,'research.pa.auditPaid','true')
    if observed:
        cmd[cmd.index('research.dynamic.GomCapabilityRun')]='research.dynamic.GomPipelineRun'
        cmd=override(cmd,'research.ctxPipeline.file',str(out/'pipeline.jsonl'))
    write_once(out/'command.json',cmd);print('CTX_PIPELINE_RUN',label,flush=True);execute(cmd,out/'run.log',timeout=900)
    receipt=checked(out,cp,500000,float('inf'));assert receipt['decoder']['dynamic.evaluations']==500000
    if observed:
        capture,=rows(out/'loaded-probe-identity.jsonl');write_once(out/'probe-identity-verified.json',verify_capture(capture,cp))
    return out,receipt


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        root=ROOT/'runs'/datetime.now().strftime('ctx-pipeline-probe-%Y%m%d-%H%M%S-%f');root.mkdir();before=protected()
        write_once(root/'protocol.json',dict(version='CTX_GOM_PIPELINE_OBSERVATION-v1',source=str(SOURCE),instance=STEM,seed=SEED,arms=ARMS,
            choice='First registered newseed;100instance has bothseeds roleHVvsIGD/Cconflict and strongPAgap, not best-outcome selection',
            scope='Read-only whole500k stage/current/teacherarchive/modelview/programend/survivor and freshadmission snapshots; no algorithm switch or new selector',
            maximumActualFE=2000000,runOrder='SHARE frozen,SHARE observed,UNIFORM frozen,UNIFORM observed',
            acceptance='Exact fullpaidSHA/finalfront/allpubliccheckpointfronts/initial100/stageFE and alluntimedsearchcounts match frozen full500k; identity and source proof. Any failure stops, no seed substitution',
            measures='Per-cycle PRE/POSTQGS, localendpoint,200pool/100survivors, internal accepted-history archive and GOM views. HV/IGD+/C and perjobFMWsupport computed offline only',
            stops='FixedCTX qualification/TIME/halfpoolingstops unchanged. Observation cannot establish causal improvement; any intervention needs new explicit preregistered pair protocol',
            observedTimeBoundary='All observer cost included but not used for any same-time performance claim',protectedBefore=before,externalTransfers=False,goalAchieved=False))
        shutil.copytree(SOURCE/STEM/'inputs',root/STEM/'inputs')
        write_once(root/STEM/'input-hashes.json',{p.name:digest(p) for p in (root/STEM/'inputs').iterdir() if p.is_file()})
        try:
            base,cp=build(root);pairs=[]
            for arm in ARMS:
                native,nr=run_one(root,base,arm,False);observed,pr=run_one(root,cp,arm,True)
                assert nr['paidSHA256']==pr['paidSHA256']
                assert nr['search']['contextGom']==pr['search']['contextGom']
                for key in nr['search']:
                    if key not in ('cooperation','contextGom'):assert nr['search'][key]==pr['search'][key]
                for key in ('dynamic.evaluations','dynamic.reusedOperations','dynamic.recomputedOperations'):assert nr['decoder'][key]==pr['decoder'][key]
                old=SOURCE/STEM/str(SEED)/('FE500K-'+arm)
                assert initial_key(native)==initial_key(observed)==initial_key(old)
                front=lambda p:[(r['checkpoint'],r['front']) for r in rows(p/'anytime.jsonl') if r['checkpointKind']=='FE']
                assert front(native)==front(observed)==front(old)
                pairs.append(dict(arm=arm,paidSHA256=nr['paidSHA256'],exactTrajectoryAndCheckpointMatch=True))
            assert fees(root)['attemptedFE']==fees(root)['successfulFE']==2000000 and fees(root)['failedFE']==0
            assert protected()==before
            write_once(root/'acceptance.json',dict(passed=True,pairs=pairs,**fees(root),observerCostNotPerformance=True,goalAchieved=False))
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**fees(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',**fees(root),goalAchieved=False));print('CTX_PIPELINE_ROOT',root,flush=True)


if __name__=='__main__':main()

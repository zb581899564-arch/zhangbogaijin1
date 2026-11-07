"""Audit lost paid supply before finite factory-pool truncation, without changing its rules."""
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import shutil

from paired_survival_bench import run_cell,FROZEN
from qgs_epoch_build import BASIS
from run_acceptance_plateau_audit import SOURCE,OBS,STEMS,SEED
from pool_retention_build import build
from pool_retention_analysis import analyze
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock


def original_identity(root):
    base=(BASIS/'classpath.txt').read_text(encoding='utf-8-sig').strip()
    prefix='org.uma.jmetal.util.research.cooperation.'
    execute(['java','-cp',f'{base};{root/"classes"}','research.dynamic.ClassResolutionProbe',
        *(prefix+n for n in ('FactoryPool','FactoryRecord','CooperationSupport'))],root/'original-pool-origins.json')
    original=read(root/'original-pool-origins.json')
    for name in ('FactoryPool','CooperationSupport'):
        assert unquote(original[prefix+name]['codeSource']).rstrip('/').endswith(FROZEN.as_posix()+'/binary/cp-0')


def replay(root,cp,stem,enabled):
    arm='ON' if enabled else 'OFF'
    out=run_cell(root,cp,{'stem':stem,'seed':SEED,'arm':arm},{'research.poolRetention.trace':str(enabled).lower(),
        'research.personal.mode':'OLDEST','research.memory.audit':'true','research.group.mode':'FULL_ROLE',
        'research.reward.mode':'GROUP','research.batch.mode':'ROLE_CROWD','research.survival.trace':'false'})
    original=SOURCE/stem/str(SEED)/'SHARE_FULL'
    for name in ('solutions.jsonl','initial-population.jsonl','local-ledger.csv'):
        assert (out/name).read_bytes()==(original/name).read_bytes(),name
    assert [r['front'] for r in rows(out/'anytime.jsonl')]==[r['front'] for r in rows(original/'anytime.jsonl')]
    receipt=rows(out/'run-receipt.jsonl')[0]
    assert receipt['paidSHA256']==rows(OBS/stem/str(SEED)/'SHARE_FULL_OFF/run-receipt.jsonl')[0]['paidSHA256']
    assert receipt['search']==rows(original/'run-receipt.jsonl')[0]['search']
    origins=rows(out/'pool-class-origins.jsonl')[0]
    assert unquote(origins['org.uma.jmetal.util.research.cooperation.FactoryPool']['codeSource']).rstrip('/').endswith((root/'classes').as_posix())
    trace=rows(out/'pool-retention.jsonl')[0];assert trace['enabled']==enabled
    if enabled:assert len(rows(out/'pool-phases.jsonl')[0]['snapshots'])==6
    write_once(out/'observation-equivalence.json',{'status':'PASS','full500kPaidSequenceSHAIdentical':True,
        'frontsGenesLedgerInitialsAndCountersIdentical':True,'actualLoadedPoolIdentityVerified':True})
    print('POOL_RETENTION_REPLAY_VERIFIED',stem,arm,{k:trace[k] for k in ('offers','peakObjectiveEnvelopeWidth','collectionSeconds')},flush=True)


def main():
    root=ROOT/'runs'/datetime.now().strftime('pool-retention-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('POOL_RETENTION_AUDIT_ROOT',root,flush=True);done=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(BASIS/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'seed':SEED,'arms':['OFF','ON'],'plannedReplayFE':2000000,
                'question':'Could already-paid compatible factory records, discarded by capacity8 truncation, supply useful combinations missing from the retained finite pool? Distinct from the failed selector-on-current-pool and phase-timing hypotheses.',
                'preserved':'Oldest/serial/stale/FULL_ROLE/group reward, original four duties, fixed FA families, cap/eta/frequency and local ledger. Only read-only source-copy observers. Full envelopes never enter proposal, acceptance, guide, ordinary pools or result archives.',
                'envelope':'Observe every record after original job-set validation and before finite-pool rejection/truncation. Retain the exact unbounded3-objective factory ND envelope, representing equal objective vectors once. Local dominance/equality is safe for the existing nonnegative cap/eta policies and independent factory max/sum composition; this is not a claim about genetic future continuations.',
                'snapshots':'Original six predefined phases: global end; M/C/E/W local ends; G2_CENTER_ENTRY. Original first and later CENTER family receivers, two per each of four families, all used without benefit resampling. No assumption that later receivers existed at earlier phases.',
                'policies':'Same existing9 cap factors0.9/1/1.1 x eta0/1/4 with fixed initial energy/wage scales, for finite8 and full paid envelopes. No new selector, weights, archive size or online candidates. Every distinct composed genome across both libraries is separately full-decoded/validated offline.',
                'score':'Own-phase and common G2-entry already-paid archive scores kept separate. Primary uses the8 later receivers at actual G2_CENTER_ENTRY, where both receiver and source were available; earlier/later cross-time cases are explanatory only.',
                'gate':'On each instance >=20% of8 predefined later-entry receivers, spanning >=2 families, must have full-envelope best single-candidate gain >=0.1% of the common paid-archive HV, with finite9 best below half that gain. A pass motivates only a fresh retention/compression protocol, not a bigger-capacity parameter scan or novelty claim.',
                'engineering':'Actual original and shadow loaded FactoryPool sources/bytes recorded. OFF/ON must reproduce frozen full500k paid sequence SHA, all FE fronts, final genes, initial population, physical ledger including restarts and search counts. Failure stops scientific interpretation.',
                'cost':'Four500k successful replays=2000000FE, failures retained. Incremental/duplicate evaluations counted normally. Returned full QA plus separate offline composition decoding and collection runtime recorded. Observed runs are not same-time efficacy evidence.',
                'scope':'Two development instances and an existing registered seed only. Not independent confirmation, fatigue specificity, original-author scores or a contribution verdict. Default mainline and all previous stop decisions preserved.'})
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs');folder=root/stem/str(SEED);folder.mkdir()
                shutil.copy2(SOURCE/stem/str(SEED)/'ledger.csv',folder/'ledger.csv')
            cp=build(root);original_identity(root)
            for stem in STEMS:
                for enabled in (False,True):replay(root,cp,stem,enabled);done.append([stem,enabled])
            result=analyze(root,cp,SEED)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completed':done,'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulReplayFE':2000000,'failedEvaluationFE':0,
        'fullSequenceEquivalence':True,'worthNewPoolRetentionProtocol':result['worthNewPoolRetentionProtocol'],
        'returnFullDecoderQA':sum(read(p)['offlineValidationDecodes'] for p in root.glob('*/*/*/summary.json')),
        'offlineAssemblyFullDecodes':result['offlineAssemblyFullDecodes']})
    print('POOL_RETENTION_AUDIT_COMPLETE',result,flush=True)


if __name__=='__main__':main()

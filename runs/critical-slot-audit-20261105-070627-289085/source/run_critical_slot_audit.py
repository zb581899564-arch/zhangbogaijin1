"""Complete paid-trace equivalent observation before any critical-factory routing intervention."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from critical_slot_build import build, SOURCE
from critical_slot_analysis import analyze

STEMS=('20_8_5_1','100_2_3_1');METHODS=('STRICT_FULL','NSGA_STRICT');SEED=10950003


def run_case(root,cp,stem,method):
    original=SOURCE/stem/method/'ANCHOR';out=root/stem/method;out.mkdir()
    cmd=read(original/'command.json');entry=cmd.index('research.dynamic.PddrIsolationRun');cmd[cmd.index('-cp')+1]=cp
    inp=root/stem/'inputs'
    for offset,name in ((1,f'{stem}.txt'),(2,'RECONSTRUCTED-setup.txt'),(3,'fatigue-input.txt')):cmd[entry+offset]=str(inp/name)
    cmd[entry+4]=str(out);shutil.copy2(cmd[entry+7],out/'ledger-input.csv');cmd[entry+7]=str(out/'ledger-input.csv')
    write_once(out/'command.json',cmd);print('CRITICAL_SLOT_REPLAY',stem,method,flush=True);execute(cmd,out/'run.log',timeout=300)
    receipt,=rows(out/'run-receipt.jsonl');old,=rows(original/'run-receipt.jsonl')
    assert receipt['attempted']==receipt['successful']==receipt['decoder']['dynamic.evaluations']==500000
    assert receipt['failed']==0 and receipt['stopReason']=='FE_LIMIT'
    assert len(receipt['paidSHA256'])==64 and receipt['paidSHA256']==old['paidSHA256']
    assert receipt['search']==old['search'] and receipt['pddr']==old['pddr']
    for key in ('dynamic.reusedOperations','dynamic.recomputedOperations','dynamic.preparedChildren'):
        assert receipt['decoder'][key]==old['decoder'][key]
    for name in ('initial-population.jsonl','local-ledger.csv','solutions.jsonl','archive-admissions.csv'):
        assert (out/name).read_bytes()==(original/name).read_bytes(),name
    assert [r['front'] for r in rows(out/'anytime.jsonl')]==[r['front'] for r in rows(original/'anytime.jsonl')]
    metrics,=rows(out/'copy-metrics.jsonl');old_metrics,=rows(original/'copy-metrics.jsonl')
    assert metrics['searchCopyAttempts']==old_metrics['searchCopyAttempts']
    write_once(out/'observation-equivalence.json',{'status':'PASS','successfulFE':500000,'failedFE':0,
        'paidSHA256':receipt['paidSHA256'],'sameAllPaidGenomesAndObjectives':True,
        'sameInitialsFrontsFinalGenomesAdmissionsLedgerSearchAcceptanceDecoderAndSnapshotCalls':True})
    return read(out/'summary.json')['offlineValidationDecodes']


def main():
    root=ROOT/'runs'/datetime.now().strftime('critical-slot-audit-%Y%m%d-%H%M%S-%f');root.mkdir();print('CRITICAL_SLOT_ROOT',root,flush=True)
    completed=[];qa=0
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(ROOT/'runs/makespan-tie-screen-20261105-025223-471920/protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'source':str(SOURCE),'methods':METHODS,'seed':SEED,'plannedReplayFE':2000000,
                'question':'How many M intra evaluations have no possible strict Cmax improvement because a different unchanged factory remains maximal? '
                           'Do those slots still contribute paid multiobjective archive value?',
                'sourceIdentity':'Resolve actual LocalSearch/SearchState/QgsLocalLedger/IntraNeighborhoods before choosing source; retain loaded.class '
                                 'SHA and JDK, inspect actual neighborhood and ledger bytecode. Shadow only observer hooks, not production.',
                'observation':'Every M intra slot before entry: actual forced factory, pre-draw factory, quota, paidFE, genome/family, factoryC/E/W, paid archive. '
                              'Every active paid candidate: other factoryC/E/W exact unchanged and impossible slots cannot lower entryCmax. '
                              'After exit: actualFE, normal/partial return, exact exit and archive. Inter/global/other roles unchanged.',
                'engineering':'6zeroFEcertificate fixtures. Each4replay500k/0failed exactly old paidSHA, initialization, everyFEfront, finalgenes, admissions, '
                              'physical ledger, search/acceptance/decoder and snapshot counts. Join observed M slots to complete real ledger. '
                              'Any engineering mismatch stops before scientific routing conclusions.',
                'scoring':'Frozen normalization/ref1.5. Sequential actual archiveHV increment by Mslot, cached offline with independent slowHV '
                          'checks; absdelta<1e-12 treated0 symmetrically. Report scalar eligibility and incidental3Dvalue separately.',
                'gate':'Eachinstance and eachmethod>=20%M intra successfulFE in pre-certified impossible slots. Only permits separate matched '
                       'routing probe. No automatic budget deletion or full algorithm promotion; incidental archivevalue reported regardless.',
                'limits':'Olddevelopmentseed and fixed replayledger, not independent confirmation, native naturalVNS or same-time experiment. '
                         'No strict C improvement does not imply no Pareto discovery or no future value. No claim unique contribution or NSGAgap explained.',
                'preserved':'No default search, Q, fourroles, family, shared rule, frozen/source inputs or ledger changed; no filetransfers.'})
            cp=build(root)
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
                for method in METHODS:qa+=run_case(root,cp,stem,method);completed.append((stem,method))
            result=analyze(root,specs,METHODS)
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedReplays':completed,'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulReplayFE':len(completed)*500000,'failedEvaluationFE':0,
        'returnFullTimelineQA':qa,'worthMatchedCriticalRoutingProbe':result['worthMatchedCriticalRoutingProbe']})
    print('CRITICAL_SLOT_COMPLETE',result,flush=True)


if __name__=='__main__':main()

"""Frozen source traces and counterfactual whole-pool retention, before any architecture change."""
from datetime import datetime
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_snapshot_anchor_audit import SOURCE, override
from global_working_build import build, ENTRY
from global_working_analysis import analyze

STEMS=('20_8_5_1','100_2_3_1');SEEDS=(11730007,11730037)


def capture(root,cp,stem,seed,enabled):
    out=root/stem/str(seed)/('ON' if enabled else 'OFF');out.mkdir()
    original=read(SOURCE/stem/'10950003/STRICT_FULL/command.json')
    index=original.index('research.dynamic.PddrIsolationRun');prefix=original[:index]
    prefix[prefix.index('-cp')+1]=cp
    for key,value in (('research.snapshot.mode','ANCHOR'),('research.snapshot.audit','false'),
                      ('research.memory.audit','true'),('research.working.capture',str(enabled).lower())):
        prefix=override(prefix,key,value)
    inp=root/stem/'inputs'
    cmd=prefix+['research.dynamic.PddrIsolationRun',str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),
        str(inp/'fatigue-input.txt'),str(out),'SHARE_JOB_ALIGNED','LINEAR',str(out.parent/'ledger.csv'),'5100',str(seed),'100','5100']
    write_once(out/'command.json',cmd);print('GLOBAL_WORKING_CAPTURE',stem,seed,enabled,flush=True);execute(cmd,out/'run.log')
    receipt,=rows(out/'run-receipt.jsonl')
    assert receipt['attempted']==receipt['successful']==receipt['decoder']['dynamic.evaluations']==5100 and receipt['failed']==0
    assert receipt['search']['initialization.evaluations']==100 and receipt['search']['global.evaluations']==5000
    assert len(receipt['paidSHA256'])==64
    if enabled:
        prior=out.parent/'OFF';old,=rows(prior/'run-receipt.jsonl')
        assert old['paidSHA256']==receipt['paidSHA256'] and old['search']==receipt['search']
        for name in ('initial-population.jsonl','solutions.jsonl','local-ledger.csv','archive-admissions.csv'):
            assert (out/name).read_bytes()==(prior/name).read_bytes()
        assert [p['front'] for p in rows(out/'anytime.jsonl')]==[p['front'] for p in rows(prior/'anytime.jsonl')]
        for key in ('dynamic.reusedOperations','dynamic.recomputedOperations'):
            assert receipt['decoder'][key]==old['decoder'][key]
        write_once(out/'observation-equivalence.json',{'status':'PASS','paidSHA256':receipt['paidSHA256'],'sameAllPaidCandidates':True,
            'sameInitialsFrontsGenomesLedgerAdmissionsAndSearchCounts':True})
    return read(out/'summary.json')['offlineValidationDecodes']


def main():
    root=ROOT/'runs'/datetime.now().strftime('global-working-audit-%Y%m%d-%H%M%S-%f');root.mkdir();print('GLOBAL_WORKING_ROOT',root,flush=True)
    completed=[];return_qa=0
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'source':str(SOURCE),'engineeringBase':str(ENTRY),
                'seeds':SEEDS,'plannedSuccessfulFE':40800,'perCaptureFE':5100,
                'question':'Does role-local global survival omit paid working states which a common100-particle '
                           'collector could retain, beyond merely changing role-local objective preference?',
                'windows':'First generation, each physical role atstep0/24/49, all12windows per source,2fresh source seeds. '
                          'Every current working100 and current batch children, no gain-based replacement.',
                'controls':'ACTUAL frozen FULL_ROLE; WITHIN_ALL identical role slots and all-objective rank/crowding; '
                           'GLOBAL_ALL common100 rank/crowding with identical overall family quotas. '
                           'All use objective-duplicate first pass then fill, exactly the frozen rule. '
                           'WITHIN_ALL must equal actualCENTER selection as a real-data scorer check.',
                'engineering':'Original actual loaded classes resolved before picking frozen source, hook-only isolated copies. '
                              'OFF/ON full paidSHA, initials/FEfronts/final genes/admissions/ledger/search/decoder counts equal. '
                              'All observed genomes have earlier paid provenance, all distinct observed genomes full-bit QA.',
                'gate':'Both instances>=20% of24windows GLOBAL_ALL beats BOTH controls by>=0.1% of common paid archiveHV, '
                       'covering>=2roles and both source seeds, and mean delta vsboth controls>=0. '
                       'Pass only permits a separate finite continuation/shared-working probe, never direct algorithm promotion.',
                'limits':'Static internal retention, not novel external discoveries or a complete alternative search. '
                         'No pbest history, parent relay, Q, budgets, kernel, family pool or shared selector changed. '
                         'Missing window/engineering failure retained; no extra seed or alternate rank/weight scan.',
                'time':'All observation and offline selection costs recorded by source run; no same-time claim.',
                'preserved':'No production changes, original materials or frozen records modified; no external transfer.'})
            oldcp=(ENTRY/'classpath.txt').read_text('utf-8');cp=build(root,oldcp)
            for stem in STEMS:
                shutil.copytree(ENTRY/stem/'inputs',root/stem/'inputs')
                for seed in SEEDS:
                    folder=root/stem/str(seed);folder.mkdir();(folder/'ledger.csv').write_text('visit,group,round,factory,paid,restarts\n',encoding='utf-8')
                    for enabled in (False,True):
                        return_qa+=capture(root,cp if enabled else oldcp,stem,seed,enabled);completed.append((stem,seed,enabled))
            result=analyze(root,cp,specs,SEEDS)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedCaptures':completed,'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':len(completed)*5100,'failedFE':0,
        'sourceReturnFullQA':return_qa,'offlinePaidGenomeFullQA':result['offlinePaidGenomeFullQA'],
        'worthIndependentSharedWorkingProbe':result['worthIndependentSharedWorkingProbe']})
    print('GLOBAL_WORKING_COMPLETE',result,flush=True)


if __name__=='__main__':
    main()

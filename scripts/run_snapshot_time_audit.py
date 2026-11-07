"""Freeze real-deadline entry acceptance before any new performance seeds."""
from datetime import datetime
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_snapshot_anchor_audit import SOURCE, STEMS, METHODS, SEED
from snapshot_time_build import build
from snapshot_time_support import execute_case

ENGINEERING=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
COST=ROOT/'runs/snapshot-cost-bench-20261105-051417-528436'


def main():
    assert read(COST/'status.json')['sharedCostGate'],'Cost gate failed; do not launch deadline experiment'
    root=ROOT/'runs'/datetime.now().strftime('snapshot-time-audit-%Y%m%d-%H%M%S-%f')
    root.mkdir();print('SNAPSHOT_TIME_AUDIT_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            write_once(root/'protocol.json',{
                'source':str(ENGINEERING),'costSource':str(COST),'instances':STEMS,'seed':SEED,
                'plannedFixedFE':2000000,'fixedModes':'Both algorithms ANCHOR, infinite T, same500000FE old ledger.',
                'scope':'New observer entry, same actual frozen search/physics classes. Deadline-only ledger permits '
                        'unspent last slot/remaining rows ONLY when context clock has reached the registered T. '
                        'Before that, original strict assertions remain. No scheduling operator or acceptance changes.',
                'acceptance':'2models x2algorithms infiniteT full paidSHA must match accepted ANCHOR source; sameFE fronts, '
                             'initials, ledger and search counters. ZeroFE forcedGLOBAL/INTER/INTRA cutoff fixtures and strict rejection. '
                             'Actual T=0 and T=0.5s probes verify fee accounting, no future genomes, partial ledger and full physical QA.',
                'timeAccounting':'Report attempted/successful/time-interrupted separately. No genuine evaluation failure allowed. '
                                 'All reported TIME fronts come from completed<=T admission evidence, never raw end archive.',
                'limits':'Engineering only. Finite cutoffs not quality comparisons or new seeds. Actual fees retained on failure.'})
            for stem in STEMS:
                shutil.copytree(ENGINEERING/stem/'inputs',root/stem/'inputs')
                shutil.copy2(ENGINEERING/stem/'ledger.csv',root/stem/'ledger.csv')
            cp=build(root,(ENGINEERING/'classpath.txt').read_text('utf-8'))
            execute(['java','-cp',cp,'org.uma.jmetal.util.research.search.DeadlineLedgerChecks',str(root/'ledger-fixtures')],root/'ledger-fixtures.log')
            for stem in STEMS:
                for method in METHODS:
                    case={'stem':stem,'seed':SEED,'template':method,'copy':'ANCHOR','label':method+'-INFINITE'}
                    out,receipt=execute_case(root,cp,case,float('inf'),True,False);completed.append(receipt)
                    old=ENGINEERING/stem/method/'ANCHOR';old_receipt,=rows(old/'run-receipt.jsonl')
                    assert receipt['paidSHA256']==old_receipt['paidSHA256']
                    assert receipt['search']==old_receipt['search']
                    assert (out/'local-ledger.csv').read_bytes()==(old/'local-ledger.csv').read_bytes()
                    assert (out/'initial-population.jsonl').read_bytes()==(old/'initial-population.jsonl').read_bytes()
                    current={r['checkpoint']:r['front'] for r in rows(out/'anytime.jsonl') if r['checkpointKind']=='FE'}
                    prior={r['checkpoint']:r['front'] for r in rows(old/'anytime.jsonl')}
                    assert current==prior
                    write_once(out/'whole-trace-equivalence.json',{'status':'PASS','paidSHA256':receipt['paidSHA256'],'originalSearchUnchanged':True})
            for method in METHODS:
                for seconds in (0.,.5):
                    case={'stem':STEMS[0],'seed':SEED,'template':method,'copy':'ANCHOR','label':method+'-CUTOFF-'+str(seconds)}
                    _,receipt=execute_case(root,cp,case,seconds,False,True);completed.append(receipt)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(r['successful'] for r in completed),
        'attemptedFE':sum(r['attempted'] for r in completed),'timeInterruptedAttempts':sum(r['timeInterruptedAttempts'] for r in completed),
        'unexpectedEvaluationFailures':0,'deadlineEntryAccepted':True})
    print('SNAPSHOT_TIME_AUDIT_COMPLETE',read(root/'status.json'),flush=True)


if __name__=='__main__':
    main()

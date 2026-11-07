"""Engineering acceptance of natural stopping, paid self-replay and actual deadline/failure boundaries."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from natural_local_build import build, ENTRY
from natural_local_support import run_case

ANCHOR=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
STEMS=('20_8_5_1','100_2_3_1');METHODS=('STRICT_FULL','NSGA_STRICT');SEED=10950003


def paid_fronts(folder):
    return {r['checkpoint']:r['front'] for r in rows(folder/'anytime.jsonl') if r['checkpointKind']=='FE' and r['reached']}


def compare_paid(out,prior):
    current,=rows(out/'run-receipt.jsonl');old,=rows(prior/'run-receipt.jsonl')
    assert current['paidSHA256']==old['paidSHA256'] and len(current['paidSHA256'])==64
    assert (out/'initial-population.jsonl').read_bytes()==(prior/'initial-population.jsonl').read_bytes()
    a,b=paid_fronts(out),paid_fronts(prior);assert all(a[k]==b[k] for k in a.keys()&b.keys())
    for key in ('dynamic.reusedOperations','dynamic.recomputedOperations','dynamic.preparedChildren'):
        assert current['decoder'][key]==old['decoder'][key]
    changed={key:{'current':current['search'].get(key),'prior':old['search'].get(key)} for key in current['search'].keys()|old['search'].keys()
             if current['search'].get(key)!=old['search'].get(key)}
    write_once(out/'paid-equivalence.json',{'status':'PASS','paidSHA256':current['paidSHA256'],
        'sameEveryPaidGenomeAndObjective':True,'sameInitialsAndAllCommonFEFronts':True,'sameDecoderReuseAndRecomputeCounts':True,
        'searchCounterDifferences':changed,'scope':'At-budget bookkeeping may finish a truncated natural slot during self-replay; '
            'all paid candidates/objectives and reported fronts must still be exact. Does not assert identical post-budget internal population.'})


def main():
    root=ROOT/'runs'/datetime.now().strftime('natural-local-audit-%Y%m%d-%H%M%S-%f');root.mkdir();print('NATURAL_LOCAL_AUDIT_ROOT',root,flush=True)
    completed=[];expected_failures=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            write_once(root/'protocol.json',{'source':str(ENTRY),'instances':STEMS,'methods':METHODS,'seed':SEED,'plannedLongFE':5000000,
                'implementation':'Only explicit record/replay entry choice, bounded checkpoint list and diagnostic last-front failure capture. '
                                 'Actual search/neighborhood/PDDR/family/sharing binaries unchanged; sameANCHORcopy for all.',
                'engineering':'Replay old FULL/NSGA on20_8matches old500kpaidSHA. Bothmodels/algorithms natural500k then ownledger500k '
                              'sameallpaidSHA,initials,commonFEfronts,decoder counts. Save end-budget counter differences explicitly. '
                              'First1/2FE, injectedobserverfailureafter2paid with actualfront, T0/.5s and zeroFEnatural GLOBAL/INTER/INTRA ledger prefixes.',
                'accounting':'Every actual attempted evaluation including duplicates charged; deadlines/faults separated. '
                             'Finite-deadline outputs onlycompleted-byTfronts with fullgenome replayQA. No failed scientific arm included.',
                'limits':'Engineering oldseed only; no quality ranking or claim naturalstopping is better. No performance runs before engineering passes.',
                'preserved':'No default production/roles/Q/operator/shared rules/input/frozenrecord changes, no transfers.'})
            cp=build(root)
            execute(['java','-cp',cp,'org.uma.jmetal.util.research.search.NaturalLedgerChecks',str(root/'ledger-fixtures')],root/'ledger-fixtures.log')
            for stem in STEMS:
                shutil.copytree(ENTRY/stem/'inputs',root/stem/'inputs');shutil.copy2(ENTRY/stem/'ledger.csv',root/stem/'ledger.csv')
            for method in METHODS:
                out,receipt=run_case(root,cp,STEMS[0],method+'-OLD_REPLAY',method,'replay',SEED,ledger=root/STEMS[0]/'ledger.csv',audit=True)
                completed.append((out,receipt));compare_paid(out,ANCHOR/STEMS[0]/method/'ANCHOR')
            for stem in STEMS:
                for method in METHODS:
                    recorded,receipt=run_case(root,cp,stem,method+'-NATURAL',method,'record',SEED,audit=True);completed.append((recorded,receipt))
                    replayed,receipt=run_case(root,cp,stem,method+'-SELF_REPLAY',method,'replay',SEED,ledger=recorded/'local-ledger.csv',audit=True)
                    completed.append((replayed,receipt));compare_paid(replayed,recorded)
            for method in METHODS:
                for limit in (1,2):
                    out,receipt=run_case(root,cp,STEMS[0],method+f'-FE{limit}',method,'record',SEED,limit=limit,audit=True)
                    completed.append((out,receipt));assert paid_fronts(out)[limit]
                out,receipt=run_case(root,cp,STEMS[0],method+'-FAIL_AFTER2',method,'record',SEED,fail_after=2)
                expected_failures.append((out,receipt));saved,=rows(out/'failure-last-front.jsonl')
                assert saved['front']==paid_fronts(root/STEMS[0]/(method+'-FE2'))[2]
                write_once(out/'expected-failure-acceptance.json',{'status':'PASS','successfulFE':2,'actualEvaluationFaults':0,'lastPaidFrontMatchesValidFE2':True})
                for seconds in (0.,.5):
                    out,receipt=run_case(root,cp,STEMS[0],method+f'-TIME{seconds}',method,'record',SEED,seconds=seconds)
                    completed.append((out,receipt))
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedValidRuns':len(completed),'expectedFailureRuns':len(expected_failures),'error':repr(error)});raise
    all_runs=completed+expected_failures
    write_once(root/'status.json',{'status':'COMPLETE','validRuns':len(completed),'expectedFailureRuns':len(expected_failures),
        'successfulFE':sum(r['successful'] for _,r in all_runs),'attemptedFE':sum(r['attempted'] for _,r in all_runs),
        'timeInterruptedAttempts':sum(r['timeInterruptedAttempts'] for _,r in all_runs),'unexpectedEvaluationFailures':0,
        'checkpointFullDecoderQA':sum(read(out/'checkpoint-validation.json')['uniqueOfflineDecodes'] for out,_ in completed),
        'naturalEntryAccepted':True})
    print('NATURAL_LOCAL_AUDIT_COMPLETE',read(root/'status.json'),flush=True)


if __name__=='__main__':main()

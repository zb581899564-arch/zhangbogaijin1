"""Bounded true-time development check after full-copy semantics and cost acceptance."""
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from run_snapshot_anchor_audit import SOURCE, STEMS
from snapshot_time_support import execute_case
from snapshot_time_analysis import analyze

ENTRY = ROOT/'runs/snapshot-time-audit-20261105-052055-989426'
COST = ROOT/'runs/snapshot-cost-bench-20261105-051417-528436'
SEEDS=(11610003,11610033,11610063)
METHODS={
    'FULL_SERIAL':('STRICT_FULL','SERIAL'), 'FULL_ANCHOR':('STRICT_FULL','ANCHOR'),
    'NSGA_SERIAL':('NSGA_STRICT','SERIAL'), 'NSGA_ANCHOR':('NSGA_STRICT','ANCHOR'),
    'LI_ANCHOR':('LI_STRICT','ANCHOR'), 'FORCE_ANCHOR':('FORCE_STRICT','ANCHOR')}
TIMES={'20_8_5_1':4.,'100_2_3_1':5.}


def execution_order():
    result=[];labels=list(METHODS)
    for s,stem in enumerate(STEMS):
        for i,seed in enumerate(SEEDS):
            offset=(s*len(SEEDS)+i)%len(labels)
            for label in labels[offset:]+labels[:offset]:
                template,copy=METHODS[label]
                result.append({'stem':stem,'seed':seed,'method':label,'label':f'{seed}-{label}',
                               'template':template,'copy':copy})
    return result


def paired_acceptance(root,case):
    stem,seed=case['stem'],case['seed'];present=[]
    for label in METHODS:
        folder=root/stem/f'{seed}-{label}'
        path=folder/'initial-population.jsonl'
        if path.exists():present.append(rows(path))
    assert all(len(data)==100 for data in present),'Initialization did not complete under the fixed T'
    assert all(data==present[0] for data in present),'Methods did not start with the same100 four-vectors'
    for prefix in ('FULL','NSGA'):
        folders=[root/stem/f'{seed}-{prefix}_{mode}' for mode in ('SERIAL','ANCHOR')]
        if not all((f/'accounting-acceptance.json').exists() for f in folders):continue
        fronts=[{p['checkpoint']:p['front'] for p in rows(f/'anytime.jsonl')
                 if p['checkpointKind']=='FE' and p['reached']} for f in folders]
        assert all(fronts[0][key]==fronts[1][key] for key in fronts[0].keys()&fronts[1].keys()),'Same-FE snapshot semantics changed'


def main():
    assert read(ENTRY/'status.json')['deadlineEntryAccepted'] and read(COST/'status.json')['sharedCostGate']
    root=ROOT/'runs'/datetime.now().strftime('snapshot-true-time-bench-%Y%m%d-%H%M%S-%f')
    root.mkdir();print('SNAPSHOT_TRUE_TIME_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances'];cases=execution_order()
            write_once(root/'protocol.json',{
                'entrySource':str(ENTRY),'costSource':str(COST),'instances':specs,'seeds':SEEDS,'methods':METHODS,
                'timeSeconds':TIMES,'order':cases,'perRunSafetyFECap':500000,'plannedSearchSeconds':162,
                'sourceScope':'Two existing development instances,3new search seeds. Physical ledger copied unchanged '
                              'from engineering seed10950003 and common to all6methods; this is ledger-conditioned, not native LS stopping.',
                'conditions':'Original reconstructed SUT/standby/strong_fast fatigue, old fixed normalization, same100 '
                             'initial vectors per seed, exactPDDR/oldestND/strictM rule, Q/duties/family/sharing unchanged. '
                             'Li explicitlyv2/FORCE/commonInitials; classic matcheddeepLS retains NSGA selection.',
                'engineering':'Whole entry accepted under infiniteT against full500000paidSHA. Every time run must '
                              'stopTIME_LIMIT before safetyFE cap, real failures0; time interruptions separately charged. '
                              'Init vectors and common reachedFE front pairs exact. Failure retained, no newT or replacement seed.',
                'outcome':'Only TIME=T last completed<=T fronts, with paid genome birth timestamps and fullQA. '
                          'All initialization/search/archive/capture costs advance clock. No postdeadline rawarchive used.',
                'gate':'Each instance FULL_ANCHOR vsFULL_SERIAL medianHV>=1%,>=2/3positive; vsNSGA_ANCHOR median>=-1%, '
                       '>=2/3pairs>=-1%; vsLI_ANCHOR andFORCE_ANCHOR median>=0,>=2/3positive. '
                       'Refs1.25/2 preserve nonnegative median for internal/Li/FORCE and>=-2% forNSGA. '
                       'IGDplus symmetric-worsening median<=5% vsall4controls. All required on both instances.',
                'metrics':'PrimaryHVreference1.5; sensitivity1.25/2. IGDplus empiricalND union of all6methods/3seeds '
                          'atT for each instance, fixed prior to outcomes and never search feedback.',
                'limits':'Cost engineering keeps same-FE trajectory, not a new scientific search contribution. '
                         'A pass only permits a separate role/sharing necessity and held-out confirmation protocol; '
                         'failure stops promotion, without changing roles/budgets/caps or adding seeds to chase wins.',
                'preserved':'Production and default mainline unchanged; no new search operator/RL, no installs or external transfers.'})
            for name in ('run_snapshot_time_bench.py','snapshot_time_analysis.py','snapshot_time_support.py'):
                shutil.copy2(Path(__file__).with_name(name),root/name)
            cp=(ENTRY/'classpath.txt').read_text('utf-8');(root/'classpath.txt').write_text(cp,encoding='utf-8')
            for stem in STEMS:
                shutil.copytree(ENTRY/stem/'inputs',root/stem/'inputs')
                shutil.copy2(ENTRY/stem/'ledger.csv',root/stem/'ledger.csv')
            for case in cases:
                out,receipt=execute_case(root,cp,case,TIMES[case['stem']]);completed.append((out,receipt))
                paired_acceptance(root,case)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),
            'successfulFEInCompletedRuns':sum(r['successful'] for _,r in completed),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','completedRuns':len(completed),
        'successfulFE':sum(r['successful'] for _,r in completed),'attemptedFE':sum(r['attempted'] for _,r in completed),
        'timeInterruptedAttempts':sum(r['timeInterruptedAttempts'] for _,r in completed),'unexpectedEvaluationFailures':0,
        'checkpointFullDecoderQA':sum(read(out/'checkpoint-validation.json')['uniqueOfflineDecodes'] for out,_ in completed),
        'worthSeparateMechanismConfirmation':result['worthSeparateMechanismConfirmation']})
    print('SNAPSHOT_TRUE_TIME_COMPLETE',[(r['stem'],r['primaryDevelopmentGate']) for r in result['instances']],flush=True)


if __name__=='__main__':
    main()

"""Common command, strict accounting and paid-genome checks for explicit natural/replay regimes."""
import csv
from run_long_budget_bridge import read, rows, write_once, execute
from run_snapshot_anchor_audit import override
from natural_local_build import FROZEN


def command(root,cp,stem,label,template,regime,seed,seconds=float('inf'),limit=500000,ledger=None,audit=False,fail_after=None):
    old=read(FROZEN/stem/'10950003'/template/'command.json');entry=old.index('research.dynamic.PddrIsolationRun')
    prefix=old[:entry];prefix[prefix.index('-cp')+1]=cp
    for key,value in (('research.snapshot.mode','ANCHOR'),('research.snapshot.audit','false'),
                      ('research.memory.audit',str(audit).lower()),('research.makespan.tie','STRICT')):
        prefix=override(prefix,key,value)
    if fail_after is not None:prefix=override(prefix,'research.natural.failAfterFE',str(fail_after))
    inp=root/stem/'inputs';out=root/stem/label
    return prefix+['research.dynamic.NaturalLocalRun',str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),
        str(inp/'fatigue-input.txt'),str(out),old[entry+5],str(limit),str(seed),
        'Infinity' if seconds==float('inf') else str(seconds),str(ledger or root/stem/'ledger.csv'),regime]


def ledger_rows(path):
    with path.open(encoding='utf-8-sig') as stream:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]


def verify(out,seconds,limit,regime,ledger_path=None,require_time=False):
    receipt,=rows(out/'run-receipt.jsonl');assert receipt['error'] is None and receipt['localLedgerMode']==regime
    assert receipt['attempted']==receipt['successful']+receipt['failed']
    assert receipt['failed']==receipt['timeInterruptedAttempts'] and 0<=receipt['timeInterruptedAttempts']<=1
    assert receipt['successful']<=receipt['decoder']['dynamic.evaluations']<=receipt['attempted']
    assert sum(receipt['search'].get(k+'.evaluations',0) for k in ('initialization','global','inter','intra'))==receipt['successful']
    if require_time:
        assert receipt['stopReason']=='TIME_LIMIT' and receipt['successful']<limit and receipt['searchSeconds']>=seconds
    else:assert receipt['stopReason']=='FE_LIMIT' and receipt['successful']==limit and receipt['failed']==0
    actual=ledger_rows(out/'local-ledger.csv')
    assert sum(r['paid'] for r in actual)==sum(receipt['search'].get(k+'.evaluations',0) for k in ('inter','intra'))
    if regime=='record':
        assert all(r['paid']>=0 and r['restarts']==0 for r in actual),'Natural mode forced a paid restart'
    else:
        expected=ledger_rows(ledger_path);assert len(actual)<=len(expected)
        for i,(a,e) in enumerate(zip(actual,expected)):
            assert all(a[k]==e[k] for k in ('visit','group','round','factory'))
            assert 0<=a['paid']<=e['paid']
            if i<len(actual)-1 or not require_time:assert a['paid']==e['paid']
        if not require_time:assert len(actual)==len(expected)
    validation=read(out/'checkpoint-validation.json')
    assert validation['status']=='passed' and validation['allReachedPointsCovered'] and validation['extraSearchFE']==0
    points=rows(out/'anytime.jsonl');genes=rows(out/'checkpoint-solutions.jsonl')
    for point in points:
        own=[g for g in genes if g['checkpointKind']==point['checkpointKind'] and g['checkpoint']==point['checkpoint']]
        if not point['reached']:assert not own and not point['front'];continue
        assert {tuple(g['objectives']) for g in own}=={tuple(p) for p in point['front']}
        assert all(g['bornFE']<=point['fe'] and g['bornSeconds']<=point['elapsedSeconds'] for g in own)
        if point['checkpointKind']=='TIME':assert point['elapsedSeconds']<=point['checkpoint'] and all(g['bornSeconds']<=point['checkpoint'] for g in own)
    write_once(out/'accounting-acceptance.json',{'status':'PASS','localLedgerMode':regime,'stopReason':receipt['stopReason'],
        'successfulFE':receipt['successful'],'attemptedFE':receipt['attempted'],'timeInterruptedAttempts':receipt['timeInterruptedAttempts'],
        'unexpectedEvaluationFailures':0,'ledgerSlots':len(actual),'checkpointFullDecoderQA':validation['uniqueOfflineDecodes'],
        'allReachedGenomesPaidAndCovered':True})
    return receipt


def run_case(root,cp,stem,label,template,regime,seed,seconds=float('inf'),limit=500000,ledger=None,audit=False,fail_after=None):
    out=root/stem/label;out.mkdir(parents=True);cmd=command(root,cp,stem,label,template,regime,seed,seconds,limit,ledger,audit,fail_after)
    write_once(out/'command.json',cmd);print('NATURAL_LOCAL_RUN',stem,label,regime,seconds,limit,flush=True)
    if fail_after is None:
        execute(cmd,out/'run.log',timeout=300)
        return out,verify(out,seconds,limit,regime,ledger,seconds!=float('inf'))
    rejected=False
    try:execute(cmd,out/'run.log',timeout=300)
    except RuntimeError:rejected=True
    assert rejected,'The explicit failure fixture did not fail'
    receipt,=rows(out/'run-receipt.jsonl');last,=rows(out/'failure-last-front.jsonl')
    assert receipt['stopReason']=='FAILED' and f'NATURAL_FAILURE_FIXTURE_AFTER_FE={fail_after}' in receipt['error']
    assert receipt['successful']==receipt['attempted']==last['successful']==last['lastObservedPaidFE']==fail_after
    assert receipt['failed']==last['failed']==0 and last['front']
    return out,receipt

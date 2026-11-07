"""Commands and accounting shared by the isolated real-deadline entry audit and benchmark."""
from run_long_budget_bridge import read, rows, write_once, execute
from run_snapshot_anchor_audit import SOURCE, override


def command(root,cp,stem,seed,template,copy_mode,out,seconds,audit=False):
    original=read(SOURCE/stem/'10950003'/template/'command.json')
    entry=original.index('research.dynamic.PddrIsolationRun')
    prefix=original[:entry];prefix[prefix.index('-cp')+1]=cp
    prefix=override(prefix,'research.snapshot.mode',copy_mode)
    prefix=override(prefix,'research.snapshot.audit','false')
    prefix=override(prefix,'research.memory.audit',str(audit).lower())
    inp=root/stem/'inputs'
    return prefix+['research.dynamic.SnapshotTimeRun',str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),
        str(inp/'fatigue-input.txt'),str(out),original[entry+5],'500000',str(seed),str(seconds),str(root/stem/'ledger.csv')]


def verify_accounting(out,ledger_path,seconds,require_time):
    receipt,=rows(out/'run-receipt.jsonl')
    assert receipt['error'] is None
    assert receipt['attempted']==receipt['successful']+receipt['failed']
    assert receipt['failed']==receipt['timeInterruptedAttempts'], 'Unexpected actual evaluation failure'
    assert 0<=receipt['timeInterruptedAttempts']<=1
    assert receipt['successful']<=receipt['decoder']['dynamic.evaluations']<=receipt['attempted']
    assert sum(receipt['search'].get(k+'.evaluations',0) for k in ('initialization','global','inter','intra'))==receipt['successful']
    if require_time:
        assert receipt['stopReason']=='TIME_LIMIT' and receipt['searchSeconds']>=seconds
        assert receipt['successful']<500000,'Capped trajectory cannot establish the requested deadline comparison'
    else:
        assert receipt['stopReason']=='FE_LIMIT' and receipt['successful']==500000 and receipt['failed']==0
    planned=[list(map(int,r.split(','))) for r in ledger_path.read_text('utf-8-sig').splitlines()[1:]]
    actual=[list(map(int,r.split(','))) for r in (out/'local-ledger.csv').read_text('utf-8-sig').splitlines()[1:]]
    assert len(actual)<=len(planned)
    for index,(observed,expected) in enumerate(zip(actual,planned)):
        assert observed[:4]==expected[:4]
        assert 0<=observed[4]<=expected[4]
        if index<len(actual)-1 or not require_time:assert observed[4]==expected[4]
    assert sum(r[4] for r in actual)==sum(receipt['search'].get(k+'.evaluations',0) for k in ('inter','intra'))
    validation=read(out/'checkpoint-validation.json');assert validation['status']=='passed' and validation['allReachedPointsCovered']
    if require_time:
        end=next(r for r in rows(out/'anytime.jsonl') if r['checkpointKind']=='TIME' and r['checkpoint']==seconds)
        assert end['reached'] and end['fe']<=receipt['successful'] and end['elapsedSeconds']<=seconds
        genes=[r for r in rows(out/'checkpoint-solutions.jsonl') if r['checkpointKind']=='TIME' and r['checkpoint']==seconds]
        assert {tuple(r['objectives']) for r in genes}=={tuple(p) for p in end['front']}
        assert all(r['bornFE']<=end['fe'] and r['bornSeconds']<=seconds for r in genes)
    write_once(out/'accounting-acceptance.json',{'status':'PASS','stopReason':receipt['stopReason'],
        'successfulFE':receipt['successful'],'timeInterruptedAttempts':receipt['timeInterruptedAttempts'],
        'unexpectedEvaluationFailures':0,'ledgerSlots':len(actual),'partialLastSlot':bool(actual and actual[-1][4]<planned[len(actual)-1][4]),
        'checkpointFullDecoderQA':validation['uniqueOfflineDecodes'],'deadlineGenomesCovered':True})
    return receipt


def execute_case(root,cp,case,seconds,audit=False,require_time=True):
    out=root/case['stem']/case['label'];out.mkdir(parents=True)
    cmd=command(root,cp,case['stem'],case['seed'],case['template'],case['copy'],out,seconds,audit)
    write_once(out/'command.json',cmd)
    print('SNAPSHOT_TRUE_TIME',case['stem'],case['label'],seconds,flush=True)
    execute(cmd,out/'run.log',timeout=240)
    return out,verify_accounting(out,root/case['stem']/'ledger.csv',seconds,require_time)

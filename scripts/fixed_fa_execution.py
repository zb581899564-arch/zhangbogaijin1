"""Fixed-FA run commands and constraint acceptance; all candidate fees stay in RunContext."""
from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from natural_local_support import command,verify,run_case
from run_snapshot_anchor_audit import override
from fixed_fa_build import ENTRY,SOURCE
from fixed_fa_inputs import assignment

METHODS={'FULL_FIXED':'STRICT_FULL','UNIFORM_FIXED':'COST_UNIFORM','NSGA_FIXED':'NSGA_STRICT'}


def run(root,cp,stem,label,method,seed,target=None,audit=False):
    out=root/stem/label;out.mkdir(parents=True)
    cmd=command(root,cp,stem,label,METHODS[method],'record',seed,limit=5100,audit=audit)
    cmd[cmd.index('research.dynamic.NaturalLocalRun')]='research.dynamic.FixedFARun'
    cmd=override(cmd,'research.fixedFA.enabled',str(target is not None).lower())
    if target is not None:cmd=override(cmd,'research.fixedFA.file',str(target))
    write_once(out/'command.json',cmd);print('FIXED_FA_CELL',stem,label,flush=True)
    execute(cmd,out/'run.log',timeout=180);receipt=verify(out,float('inf'),5100,'record')
    fixed=read(out/'fixedfa-constraint.json');assert fixed['evaluationAttemptsChecked']==5100 and fixed['createdInitials']==100
    assert fixed['driftRejected']==0 and not fixed['evaluationProjectionUsed'] and fixed['enabled']==(target is not None)
    assert receipt['search']['global.evaluations']==5000 and receipt['search']['initialization.evaluations']==100
    assert receipt['search'].get('inter.evaluations',0)==receipt['search'].get('intra.evaluations',0)==0
    mask=fixed['mutationMask'];assert mask['enabled']==fixed['enabled']
    if target is not None:
        desired=tuple(int(v) for v in target.read_text('utf-8').strip().split(','));assert tuple(fixed['fixedFactoryByJob'])==desired
        assert all(assignment(r)==desired for name in ('initial-population.jsonl','checkpoint-solutions.jsonl') for r in rows(out/name))
        field='classicFactoryMutationsSkipped' if method=='NSGA_FIXED' else 'alignedFactoryMutationsSkipped'
        assert mask[field]>0
    else:assert mask['classicFactoryMutationsSkipped']==mask['alignedFactoryMutationsSkipped']==0
    if method!='NSGA_FIXED':assert all(receipt['search'][f'qgs.g{g}.updates']==50 for g in (1,2,3,4))
    return out,receipt


def equivalent(old,new):
    a,b=(rows(p/'run-receipt.jsonl')[0] for p in (old,new))
    assert a['paidSHA256']==b['paidSHA256'] and a['search']==b['search']
    ops=lambda r:{k:v for k,v in r['decoder'].items() if not k.endswith('Nanos')}
    assert ops(a)==ops(b)
    for name in ('initial-population.jsonl','local-ledger.csv'):assert (old/name).read_bytes()==(new/name).read_bytes()
    def fronts(p):return [(r['checkpoint'],r['front']) for r in rows(p/'anytime.jsonl') if r['checkpointKind']=='FE']
    def genes(p):return [{k:r[k] for k in ('checkpoint','JS','FA','MA','WA','objectives','bornFE')} for r in rows(p/'checkpoint-solutions.jsonl') if r['checkpointKind']=='FE']
    assert fronts(old)==fronts(new) and genes(old)==genes(new)
    write_once(new/'off-equivalence.json',{'status':'PASS','successfulFEPerArm':5100,'completePaidSequenceEqual':True,
        'initialsFEFrontsGenomesLedgerAndSearchDecodeOperationsEqual':True})


def engineering(root,cp,specs,contexts):
    import shutil
    completed=[];work=root/'engineering'
    for spec in specs:
        stem=spec['stem'];shutil.copytree(SOURCE/stem/'inputs',work/stem/'inputs')
        for method in ('FULL_FIXED','NSGA_FIXED'):
            baseline,receipt=run_case(work,(ENTRY/'classpath.txt').read_text('utf-8'),stem,method+'-BASE',METHODS[method],'record',12390003,limit=5100,audit=True)
            completed.append((baseline,receipt));out,receipt=run(work,cp,stem,method+'-MASK_OFF',method,12390003,audit=True)
            completed.append((out,receipt));equivalent(baseline,out)
    stem=specs[0]['stem'];context=contexts[stem][0];target=root/stem/'contexts'/(context['contextId']+'.txt')
    inp=root/stem/'inputs';folder=root/'guard-fixture'
    cmd=['java','-Xms32m','-Xmx2g','-Dresearch.fixedFA.enabled=true','-Dresearch.fixedFA.file='+str(target),'-cp',cp,
         'research.dynamic.FixedFAGuardChecks',str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(folder)]
    write_once(root/'guard-command.json',cmd);execute(cmd,root/'guard-run.log');guard=read(folder/'receipt.json')
    assert guard['status']=='PASS_EXPECTED_GUARD_FAILURE' and guard['successfulFE']==2 and guard['expectedFailures']==1
    assert guard['constraint']['driftRejected']==1 and guard['lastValidFront']
    write_once(root/'engineering-gate.json',{'status':'PASS','offEquivalenceRuns':8,'offSuccessfulFE':40800,
        'guardSuccessfulFE':2,'guardExpectedFailedFE':1,'guardFullQA':2,'noEvaluationProjection':True,
        'limits':'Global conditional kernel only. All performance candidates must also pass per-evaluation FA guard and common initial acceptance.'})
    return completed,guard

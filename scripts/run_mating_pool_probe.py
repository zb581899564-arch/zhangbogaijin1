"""Freeze and run actual pre-batch sources and same-kernel mating-source controls, locally only."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from mating_probe_build import build
from mating_pool_analysis import analyze, METHODS

SOURCE=ROOT/'runs/global-working-audit-20261105-055724-963327'
STEMS=('20_8_5_1','100_2_3_1');SEEDS=(11730007,11730037);PROBE_SEED=11950003


def capture(root,cp,stem,seed):
    prior=SOURCE/stem/str(seed)/'OFF';out=root/stem/str(seed)/'capture';out.mkdir(parents=True)
    cmd=read(prior/'command.json');entry=cmd.index('research.dynamic.PddrIsolationRun');cmd[cmd.index('-cp')+1]=cp
    inp=root/stem/'inputs'
    for offset,name in ((1,f'{stem}.txt'),(2,'RECONSTRUCTED-setup.txt'),(3,'fatigue-input.txt')):cmd[entry+offset]=str(inp/name)
    cmd[entry+4]=str(out);cmd[entry+7]=str(out.parent/'ledger.csv')
    (out.parent/'ledger.csv').write_text('visit,group,round,factory,paid,restarts\n',encoding='utf-8')
    write_once(out/'command.json',cmd);print('MATING_SOURCE_CAPTURE',stem,seed,flush=True);execute(cmd,out/'run.log')
    receipt,=rows(out/'run-receipt.jsonl');old,=rows(prior/'run-receipt.jsonl')
    assert receipt['attempted']==receipt['successful']==5100 and receipt['failed']==0
    assert receipt['paidSHA256']==old['paidSHA256'] and receipt['search']==old['search']
    for name in ('initial-population.jsonl','solutions.jsonl','local-ledger.csv','archive-admissions.csv'):
        assert (out/name).read_bytes()==(prior/name).read_bytes(),name
    assert [r['front'] for r in rows(out/'anytime.jsonl')]==[r['front'] for r in rows(prior/'anytime.jsonl')]
    for key in ('dynamic.reusedOperations','dynamic.recomputedOperations'):assert receipt['decoder'][key]==old['decoder'][key]
    write_once(out/'observation-equivalence.json',{'status':'PASS','paidSHA256':receipt['paidSHA256'],
        'sameAllPaidCandidatesInitialsFrontsFinalGenomesAdmissionsLedgerAndCounts':True,'archiveMirrorExactAtEveryCapturedBoundary':True})
    return read(out/'summary.json')['offlineValidationDecodes']


def prepare(root,stem):
    contexts=[];tsv=[]
    for seed in SEEDS:
        out=root/stem/str(seed)/'capture';initial=[p for p in rows(out/'mating-initial-points.jsonl') if p['category']==0]
        windows=rows(out/'mating-source-pools.jsonl');assert [w['step'] for w in windows]==[0,24,49]
        for window in windows:
            current=[p for p in window['parents'] if p['category']==0];assert len(current)==len(initial)==80
            assert sum(p['role']=='CENTER' for p in current)==47
            id=f'c{len(contexts)}';pre=window['preBatchFE']
            assert all(p['earliestKnownPaidFE']<=pre for p in current+initial)
            contexts.append({'contextId':id,'seed':seed,'step':window['step'],'preBatchFE':pre,
                'background':window['preBatchArchive'],'current':current,'initial':initial})
            for scope,points in (('CURRENT',current),('INITIAL',initial)):
                for p in points:tsv.append('\t'.join([id,scope,p['role'],*(','.join(map(str,p[k])) for k in ('JS','FA','MA','WA','objectives'))]))
    assert len(contexts)==6
    write_once(root/stem/'contexts.json',contexts)
    (root/stem/'contexts.tsv').write_text('\n'.join(c['contextId'] for c in contexts)+'\n',encoding='utf-8')
    (root/stem/'donors.tsv').write_text('\n'.join(tsv)+'\n',encoding='utf-8')
    return 6*(160+4*16*8)


def main():
    root=ROOT/'runs'/datetime.now().strftime('mating-pool-probe-%Y%m%d-%H%M%S-%f');root.mkdir();print('MATING_POOL_ROOT',root,flush=True)
    completed=[];receipts=[];return_qa=0
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'source':str(SOURCE),'sourceSeeds':SEEDS,'probeSeed':PROBE_SEED,
                'candidate':'SHARED','methods':METHODS,'plannedSourceFE':20400,'plannedProbeFE':8064,'plannedChildFE':6144,
                'question':'Does a currently evolved cross-role donor pool improve new CENTER offspring beyond within-CENTER, '
                           'uniform cross-role donors and the equally large initial pool, using the identical classic generation kernel?',
                'capture':'Observer-only replay4*5100 with original OFF paidSHA and complete observable outputs equal. '
                          'Mirror exact actual paid archive. Before CENTER step0/24/49 capture current100, roles, family and earliest paid provenance; '
                          'initial100 separately captured after decomposition. No after-batch archive as pre-batch background.',
                'sampling':'2development instances,2reused source seeds,3fixed windows. Each8freeCENTER recipients at floor(i*46/7), '
                           '16paired construction noises. All outcomes equally included, no gain-based parent/window replacement.',
                'rules':'WITHIN fresh actual NSGA score/tournament on current47freeCENTER;SHARED same on current80free across roles; '
                        'RANDOM_SHARED uniform on same80;INITIAL_SHARED same score/tournament on initial80free. '
                        'Actual setting0 ClassicKernelBridge.child(fixedRecipient,donor) and common repair. '
                        'Separate paired donor and construction RNG, not claimed identical donor or descendant stream.',
                'fees':'Percontext160paid input replays, duplicates included, then512paid children. Full timelineQA on every input and child. '
                       'Actual score recomputed every8-child batch, all score/draw/kernel/repair/evaluation costs retained. No speculative amortization.',
                'gate':'Both instances>=24/48informative recipients; SHARED mean single-addedHV>=10%overWITHIN andINITIAL_SHARED '
                       'and>=5%overRANDOM_SHARED,>=27/48parentwins vsWITHIN; eachsource seed positive and eachstep aggregate nonnegative '
                       'vsWITHIN. Median score-amortized-peractual8child+draw+kernel+evaluation callcost ratio<=1.25 vsWITHIN. '
                       'Allnecessary. Failure stops this fixed source mechanism without pool size/window/tournament/kernel/seed tuning.',
                'limits':'OnlyfreeCENTER, conditional one-child value, not originalNSGA inherited union scores or actual CENTER replacement. '
                         'Reused sources, not independent confirmation, role specificity, sharing contribution, novelty or same-time advantage. '
                         'A pass only permits another pre-registered closed-loop/role-ablation experiment.',
                'preserved':'No production/default mainline, original materials, frozen records, Q, duty, family or sharing changes; no network transfer.'})
            cp=build(root)
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
                for seed in SEEDS:return_qa+=capture(root,cp,stem,seed);completed.append((stem,seed))
            for stem in STEMS:
                expected=prepare(root,stem);inp=root/stem/'inputs';out=root/stem/'probe'
                cmd=['java','-Xms32m','-Xmx2g','-Dresearch.snapshot.mode=ANCHOR','-cp',cp,'research.dynamic.MatingPoolProbe',
                     str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),
                     str(root/stem/'contexts.tsv'),str(root/stem/'donors.tsv'),str(out),str(PROBE_SEED)]
                write_once(root/stem/'command.json',cmd);print('MATING_OFFSPRING_PROBE',stem,flush=True);execute(cmd,root/stem/'run.log',timeout=240)
                receipt,=rows(out/'receipt.jsonl');assert receipt['successfulFE']==expected and receipt['failedFE']==0;receipts.append(receipt)
            result=analyze(root,specs)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedCaptures':completed,'completedProbeInstances':len(receipts),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','sourceSuccessfulFE':len(completed)*5100,
        'probeSuccessfulFE':sum(r['successfulFE'] for r in receipts),'failedEvaluationFE':0,'sourceReturnFullQA':return_qa,
        'probeFullTimelineQA':sum(r['fullTimelineQA'] for r in receipts),'worthFreshClosedLoop':result['worthFreshClosedLoop']})
    print('MATING_POOL_COMPLETE',result,flush=True)


if __name__=='__main__':main()

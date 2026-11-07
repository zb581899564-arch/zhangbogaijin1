"""Conventional target-directed personal guides, tested before any new memory or framework implementation."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from research.search_mechanism.campaign import _case_fields
from reference_history_analysis import analyze, METHODS

SOURCE=ROOT/'runs/personal-context-probe-20261105-013210-769156'
KERNEL=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
STEMS=('20_8_5_1','100_2_3_1');SEEDS=(10280003,10280033);PROBE_SEED=11840003


def prepare(root,stem):
    shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs');cases=[];histories=[];scales=[];lines=[]
    for seed in SEEDS:
        folder=SOURCE/stem/str(seed)
        source,=rows(folder/'ON/teacher-cohorts.jsonl');off,=rows(folder/'OFF/run-receipt.jsonl');on,=rows(folder/'ON/run-receipt.jsonl')
        assert off['paidSHA256']==on['paidSHA256'] and len(off['paidSHA256'])==64
        cohort=next(c for c in source['cohorts'] if c['role']=='CENTER')
        initial=rows(folder/'ON/initial-population.jsonl');assert len(initial)==100
        mean=np.mean([p['objectives'] for p in initial],axis=0);assert np.all(mean>0)
        for row in sorted(cohort['parents'],key=lambda r:r['parentIndex']):
            id=f'p{len(cases)}';history=row['personalHistory'];assert history
            key=lambda g:tuple(tuple(g[k]) for k in ('JS','FA','MA','WA','objectives'))
            assert key(history[0])==key(row['personal'])
            case={'caseId':id,'seed':seed,'step':cohort['step'],'source':{'parent':row['parent'],'personal':row['personal'],
                'global':row['nativeLeader'],'history':history,'background':cohort['background'],'initialMeanScales':mean.tolist()}}
            cases.append(case);lines.append(_case_fields({'caseId':id,'parent':row['parent'],'personal':row['personal'],'global':row['nativeLeader']}))
            for h in history:histories.append('\t'.join([id,*(','.join(map(str,h[k])) for k in ('JS','FA','MA','WA','objectives'))]))
            scales.append(id+'\t'+','.join(map(str,mean)))
    assert len(cases)==16
    write_once(root/stem/'cases.json',cases)
    for name,content in (('cases.tsv',lines),('histories.tsv',histories),('scales.tsv',scales)):
        (root/stem/name).write_text('\n'.join(content)+'\n',encoding='utf-8')
    return 16*(3+55*2*len(METHODS))+len(histories)


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    for name in ('ReferenceHistoryChoice','ReferenceHistoryProbe','NeutralProbeSupport','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('run_reference_history_probe.py','reference_history_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    shutil.copytree(ROOT/'research/composition_oracle',source/'composition_oracle',ignore=shutil.ignore_patterns('__pycache__'))
    base=(KERNEL/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


def main():
    root=ROOT/'runs'/datetime.now().strftime('reference-history-probe-%Y%m%d-%H%M%S-%f');root.mkdir();print('REFERENCE_HISTORY_ROOT',root,flush=True)
    receipts=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'source':str(SOURCE),'sourceSeeds':SEEDS,'probeSeed':PROBE_SEED,
                'candidate':'DIR_CHEBY','methods':METHODS,'contexts':'All16 saved CENTER free parents per instance, first action2 step>=24; reused development data, not new confirmation.',
                'directions':'Every strictly-positive integer triple summing12, divided12: exactly55 directions, matching original CENTER size. '
                             'All directions equally averaged, none selected by outcome; no resolution/weight sweep.',
                'rules':'OLDEST original;CURRENT parent;RANDOM independent uniform history;DIR_SUM same directions weighted sum; '
                        'BALANCED equal-weight Chebyshev;DIR_CHEBY direction weighted Chebyshev. Zero ideal, per-source initial100 '
                        'objective means as scales, ties oldest. Only existing personal teacher varies; native global teacher and actual kernel fixed.',
                'fees':'Every source parent/personal/global plus every history entry replayed once per case and paid, duplicates included. '
                       'Then6methods*55weights*2paired construction samples evaluated percase, every child complete timeline QA. '
                       'Selector scans/copy costs counted perchild; no speculative amortization. No new source search or training labels.',
                'engineering':'Exact source objectives, original oldest agrees with history0, all known inputs covered by pre-batch '
                              'paid archive. Kernel does not mutate sources; all new children keep legal repaired4vectors and exactfull timelines.',
                'gate':'Both instances>=8informative actual parents; candidate>=10%mean addedHV overOLDEST,>=5%over EACH '
                       'CURRENT/RANDOM/DIR_SUM/BALANCED;>=9/16parent wins overOLDEST and positive aggregate in both source seeds. '
                       'Median selector+kernel+evaluation callcost<=1.10 vsOLDEST. All necessary; failure stops this fixed target rule '
                       'without alternate lattice/weights/window/scales or promoting a control after outcomes.',
                'limits':'One-offspring conditional value, not stable lineage direction assignment, whole algorithm, same-time superiority, '
                         'role/sharing benefit or novelty. Reference-vector/decomposition MOPSO is established; this is an ordinary control hypothesis.',
                'literature':['https://link.springer.com/article/10.1007/s40747-020-00134-7','https://pmc.ncbi.nlm.nih.gov/articles/PMC5305220/'],
                'preserved':'No default mainline, Q, role duties, family protection, shared pool, decoder or search budget changed; no external transfers.'})
            expected={stem:prepare(root,stem) for stem in STEMS};write_once(root/'planned-fees.json',expected)
            cp=build(root)
            for stem in STEMS:
                inp=root/stem/'inputs';out=root/stem/'probe'
                cmd=['java','-Xms32m','-Xmx2g','-Dresearch.snapshot.mode=ANCHOR','-cp',cp,'research.dynamic.ReferenceHistoryProbe',
                    str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),
                    str(root/stem/'cases.tsv'),str(root/stem/'histories.tsv'),str(root/stem/'scales.tsv'),str(out),str(PROBE_SEED)]
                write_once(root/stem/'command.json',cmd);execute(cmd,root/stem/'run.log',timeout=240)
                receipt,=rows(out/'receipt.jsonl');assert receipt['successfulFE']==expected[stem] and receipt['failedFE']==0;receipts.append(receipt)
            result=analyze(root,specs)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedInstances':len(receipts),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(r['successfulFE'] for r in receipts),'failedFE':0,
        'candidateFullTimelineQA':sum(r['candidateFullTimelineQA'] for r in receipts),'worthFreshClosedLoop':result['worthFreshClosedLoop']})
    print('REFERENCE_HISTORY_COMPLETE',result,flush=True)


if __name__=='__main__':
    main()

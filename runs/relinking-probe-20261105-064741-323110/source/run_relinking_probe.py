"""Frozen constructive benchmark: all intermediate evaluations are charged and replayed exactly."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from relinking_analysis import analyze, METHODS

SOURCE=ROOT/'runs/mating-pool-probe-20261105-062648-478040'
KERNEL=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
STEMS=('20_8_5_1','100_2_3_1');PROBE_SEED=12060003
ROLES=('MAKESPAN','ENERGY','WORKER_COST')


def prepare(root,stem):
    shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs');contexts=read(SOURCE/stem/'contexts.json');pairs=[];lines=[]
    for context in contexts:
        center=[p for p in context['current'] if p['role']=='CENTER'];assert len(center)==47
        for recipient in range(8):
            parent=center[recipient*46//7]
            for role in ROLES:
                pool=[p for p in context['current'] if p['role']==role];assert len(pool)==11
                teacher=pool[recipient*10//7];assert parent['category']==teacher['category']==0
                assert all(p['earliestKnownPaidFE']<=context['preBatchFE'] for p in (parent,teacher))
                id=f'p{len(pairs)}';pairs.append({'pairId':id,'contextId':context['contextId'],'seed':context['seed'],
                    'step':context['step'],'recipient':recipient,'teacherRole':role,'parent':parent,'teacher':teacher})
                lines.append('\t'.join([id,context['contextId'],str(recipient),role,
                    *(','.join(map(str,p[k])) for p in (parent,teacher) for k in ('JS','FA','MA','WA','objectives'))]))
    assert len(pairs)==144
    write_once(root/stem/'pairs.json',pairs)
    write_once(root/stem/'contexts.json',[{k:c[k] for k in ('contextId','seed','step','preBatchFE','background')} for c in contexts])
    (root/stem/'pairs.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return len(pairs)*(2+4*int(stem.split('_')[0]))


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    for name in ('FactoryCoverTransfer','CommittedRelinkingPath','RelinkingEngineering','RelinkingProbe','NeutralProbeSupport','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('run_relinking_probe.py','relinking_analysis.py'):shutil.copy2(Path(__file__).with_name(name),source)
    shutil.copytree(ROOT/'research/composition_oracle',source/'composition_oracle',ignore=shutil.ignore_patterns('__pycache__'))
    base=(KERNEL/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


def protocol(specs):
    return {'instances':specs,'source':str(SOURCE),'probeSeed':PROBE_SEED,'candidate':'COVER_PATH','methods':METHODS,
        'plannedSuccessfulFE':69696,'plannedSourceFE':0,'plannedFullTimelineQA':69696,
        'question':'Can committed joint paths create useful intermediate solutions beyond known endpoints, more efficiently than one-shot joint crossover?',
        'sampling':'All6existing pre-batch CENTER windows,8equally spaced freeCENTER parents per window; freeM/E/W donors floor(i*10/7) '
                   'within the11current members. No quality-based donor or window selection.144pairs but48recipient clusters perinstance.',
        'construction':'Commit each targetJS job: put job at its target absolute position by a job-aligned swap, transfer its fullFA/MA/WA. '
                       'If this empties a factory, transfer smallest-id uncommitted job targeting that factory, until coverage restored. '
                       'Each auxiliary transfer corrects another targetFA; committed positions/tuples remain fixed. Endpoints match known teacher.',
        'controls':'REPAIR_PATH same commit order but ordinary common repair; laststep restores target to match known endpoint, all restoration work charged. '
                   'RANDOM_PATH same cover rule, uniformly shuffled commit order. CLASSIC Nindependent actualsetting0 offspring from same fixed endpoints. '
                   'All methods Npaid candidates; no uncharged lookahead or suffix rollout. Copy, construction, generic repair and evaluation measured.',
        'engineering':'Before outcome evaluation,4assignment fixtures and every actual pair/path checked for encoding, coverage, untouched inputs and endpoint. '
                      'Every guarded input and intermediate then compared bit-exact full timeline; known endpoints earn zero pre-batch novelty.',
        'scoring':'Joint conditional HV gain of all Nintermediates per method, not sum of single-point gains. '
                  'Average3teacher roles per recipient;48clusters perinstance. Frozen normalization, ref1.5 primary and1.25/2sensitivity.',
        'gate':'Both instances>=24informative recipients; COVER_PATH mean union-addedHV>=10%overCLASSIC,>=5%overRANDOM_PATH,>=-1%overREPAIR_PATH; '
               '>=27/48recipient wins vsCLASSIC andvsRANDOM_PATH; both source seeds positive vsboth; eachstep aggregate nonnegative vsCLASSIC; '
               'reference1.25/2 directions vsCLASSIC/RANDOM_PATH positive. Median construction+evaluation+actualsetup cost ratio<=1.25 vsCLASSIC. '
               'All necessary, no seed/order/donor/length retuning on failure. Pass only permits separate closed-loop and supply-origin ablation.',
        'novelty':'Ordinary path relinking is established. Cover chains are feasibility engineering, not an independent novelty claim; '
                  'REPAIR_PATH near-equivalence would not establish special gain from cover. No claim four-role origin or fatigue adds independent value yet.',
        'literature':[{'url':'https://www.sciencedirect.com/science/article/pii/S0305054824002557/pdf',
                       'doi':'10.1016/j.cor.2024.106783','scope':'Publisher search-extracted abstract/intro only; direct full page403, no full-method audit.'}],
        'timeLimits':'Micro cost necessary only; shared probe archive and offline QA interleaved. No same-time whole-method claim.',
        'preserved':'No production/default, original/frozen inputs, role, Q, family, shared selector, population or budget policy changed; no file transfers.'}


def main():
    root=ROOT/'runs'/datetime.now().strftime('relinking-probe-%Y%m%d-%H%M%S-%f');root.mkdir();print('RELINKING_ROOT',root,flush=True)
    receipts=[];engineering=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            assert read(SOURCE/'status.json')['status']=='COMPLETE'
            specs=read(SOURCE/'protocol.json')['instances'];write_once(root/'protocol.json',protocol(specs))
            expected={stem:prepare(root,stem) for stem in STEMS};assert sum(expected.values())==69696
            write_once(root/'planned-fees.json',expected);cp=build(root)
            for stem in STEMS:
                inp=root/stem/'inputs';report=root/stem/'engineering.json'
                cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'research.dynamic.RelinkingEngineering',str(inp/f'{stem}.txt'),
                     str(inp/'RECONSTRUCTED-setup.txt'),str(root/stem/'pairs.tsv'),str(report)]
                write_once(root/stem/'engineering-command.json',cmd);execute(cmd,root/stem/'engineering.log')
                result=read(report);assert result['status']=='PASS' and result['searchFE']==result['decodes']==0;engineering.append(result)
            for stem in STEMS:
                inp=root/stem/'inputs';out=root/stem/'probe'
                cmd=['java','-Xms32m','-Xmx2g','-Dresearch.snapshot.mode=ANCHOR','-cp',cp,'research.dynamic.RelinkingProbe',
                    str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(root/stem/'pairs.tsv'),str(out),str(PROBE_SEED)]
                write_once(root/stem/'command.json',cmd);print('RELINKING_PAID_PROBE',stem,flush=True);execute(cmd,root/stem/'run.log',timeout=300)
                receipt,=rows(out/'receipt.jsonl');assert receipt['successfulFE']==expected[stem] and receipt['failedFE']==0
                assert receipt['fullTimelineQA']==expected[stem];receipts.append(receipt)
            result=analyze(root,specs)
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedEngineering':len(engineering),
            'completedProbeInstances':len(receipts),'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(r['successfulFE'] for r in receipts),'failedEvaluationFE':0,
        'fullTimelineQA':sum(r['fullTimelineQA'] for r in receipts),'zeroFEEngineeringSteps':sum(r['completeEncodingSteps'] for r in engineering),
        'worthFreshClosedLoop':result['worthFreshClosedLoop']})
    print('RELINKING_COMPLETE',result,flush=True)


if __name__=='__main__':main()

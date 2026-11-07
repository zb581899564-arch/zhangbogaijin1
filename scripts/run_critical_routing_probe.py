"""Matched finite continuation before changing either four-role or NSGA-II local factory routing."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from critical_routing_analysis import analyze

SOURCE=ROOT/'runs/critical-slot-audit-20261105-070658-179204'
KERNEL=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
STEMS=('20_8_5_1','100_2_3_1');METHODS=('STRICT_FULL','NSGA_STRICT');PROBE_SEED=12280003


def prepare(root,stem):
    shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs');cases=[];lines=[]
    for method in METHODS:
        assert read(SOURCE/stem/method/'observation-equivalence.json')['status']=='PASS'
        candidates=[r for r in rows(SOURCE/stem/method/'critical-slots.jsonl') if r['round']==0 and r['entry']['family'] is None and r['paid']>0]
        assert len(candidates)>=8
        for i in range(8):
            r=candidates[i*(len(candidates)-1)//7];p=r['entry'];id=f'c{len(cases)}'
            cases.append({'caseId':id,'sourceMethod':method,'sourceVisit':r['visit'],'sourceBeforeFE':r['beforeFE'],
                'factory':r['factory'],'impossible':r['strictMakespanImprovementImpossible'],'parent':p,'background':r['beforeArchive']})
            lines.append('\t'.join([id,method,str(r['factory']),*(','.join(map(str,p[k])) for k in ('JS','FA','MA','WA','objectives'))]))
    write_once(root/stem/'cases.json',cases);(root/stem/'cases.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return len(cases)*2*3*257


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    original=Path(read(SOURCE/'original-identity/local-source.json')['source']);body=original.read_text('utf-8')
    old='    private PermutationSolution<Integer> vns(PermutationSolution<Integer> parent, int factory,\n            Direction direction, List<PermutationSolution<Integer>> reference, int[] remaining) {'
    body=replace(body,old,old.replace('    private ','    ',1));(source/'LocalSearch.java').write_text(body,encoding='utf-8')
    for name in ('CriticalRoutingKernel','CriticalRoutingProbe','NeutralProbeSupport','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('run_critical_routing_probe.py','critical_routing_analysis.py'):shutil.copy2(Path(__file__).with_name(name),source)
    shutil.copytree(ROOT/'research/composition_oracle',source/'composition_oracle',ignore=shutil.ignore_patterns('__pycache__'))
    base=(KERNEL/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


def main():
    root=ROOT/'runs'/datetime.now().strftime('critical-routing-probe-%Y%m%d-%H%M%S-%f');root.mkdir();print('CRITICAL_ROUTING_ROOT',root,flush=True);receipts=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            assert read(SOURCE/'status.json')['worthMatchedCriticalRoutingProbe']
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'source':str(SOURCE),'probeSeed':PROBE_SEED,'plannedSuccessfulFE':49344,
                'question':'Can current-critical-factory routing recover useful M-task search value under equal actual FE, including incidental3Dvalue?',
                'sampling':'For eachinstance and FULL/NSGA source, first M intra slot of each free visit, then8equally spaced such entries. '
                           'No selection by criticality/improvement, no protected families.2paired construction replicas perparent.',
                'rules':'FROZEN actual source slotfactory; RANDOM uniform perVNSrestart; CRITICAL current maximum factory perVNSrestart, '
                        'retain fallback when tied else lowestid. Only factory argument changes, actual frozen VNS/strict acceptance unchanged. '
                        'A separate paired policy RNG is drawn equally for all modes; it never advances native proposal RNG.',
                'fees':'Eachtrial1paid exactparentreplay+256VNSactual evaluations, duplicates included.16parents*2rep*3modes*257 perinstance. '
                       'Every paid fulltimeline independently replayed after run, QA timing separated. Source archive only offline scoring.',
                'scoring':'All actual paid discoveries jointHV vs true source pre-slot archive, original norm/ref1.5 plus1.25/2. '
                          'Minimum paidCmax equals returned scalar incumbent; certified FROZEN cannot improve initialC. No peer archive or cooperative feedback in this local task.',
                'gate':'All4instance/source groups>=4/8informative parents,>=5/8parentwins vsRANDOM; '
                       'mean jointaddedHV>=1.10times BOTH FROZEN/RANDOM, absolute>1e-10 and mean gain>=0.1%ofbackgroundHV; '
                       'meanC improvement no worse thanboth. Reference1.25/2 gains positive vsboth. Median full finite-task '
                       'clock ratioCRITICAL/RANDOM<=1.10. Allnecessary; failed fixed routing stops without changing quota, routing interval, seeds or neighbors.',
                'limits':'Development contexts, not full algorithms, natural stopping, trueTIME_LIMIT or independent confirmation. '
                         'Common routing, so any generic gain must also be offered to NSGA; no new novelty or four-role-specific claim. '
                         'Only a complete gate pass permits a separately registered matched closed-loop experiment.',
                'preserved':'No mainline, original/frozen records, Q, duty, family/shared rules or original ledger changed; no filetransfer.'})
            expected={stem:prepare(root,stem) for stem in STEMS};assert sum(expected.values())==49344
            write_once(root/'planned-fees.json',expected);cp=build(root)
            for stem in STEMS:
                inp=root/stem/'inputs';out=root/stem/'probe'
                cmd=['java','-Xms32m','-Xmx2g','-Dresearch.snapshot.mode=ANCHOR','-cp',cp,'research.dynamic.CriticalRoutingProbe',
                    str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(root/stem/'cases.tsv'),str(out),str(PROBE_SEED)]
                write_once(root/stem/'command.json',cmd);print('CRITICAL_ROUTING_TASKS',stem,flush=True);execute(cmd,root/stem/'run.log',timeout=300)
                receipt,=rows(out/'receipt.jsonl');assert receipt['successfulFE']==expected[stem]==receipt['fullTimelineQA'] and receipt['failedFE']==0;receipts.append(receipt)
            result=analyze(root,specs)
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedInstances':len(receipts),'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(r['successfulFE'] for r in receipts),'failedFE':0,
        'fullTimelineQA':sum(r['fullTimelineQA'] for r in receipts),'worthMatchedClosedLoop':result['worthMatchedClosedLoop']})
    print('CRITICAL_ROUTING_COMPLETE',result,flush=True)


if __name__=='__main__':main()

"""Existence and direct-control audit on all predeclared paid checkpoint fronts, not a new mechanism run."""
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes

SOURCE=ROOT/'runs/snapshot-true-time-bench-20261105-052344-318911'
STEMS=('20_8_5_1','100_2_3_1');METHODS=('FULL_ANCHOR','NSGA_ANCHOR');SEEDS=(11610003,11610033,11610063)
CHECKS=(100,5100,100000)


def prepare(root,stem):
    shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
    unique={}
    for seed in SEEDS:
        for method in METHODS:
            folder=SOURCE/stem/f'{seed}-{method}'
            for row in rows(folder/'checkpoint-solutions.jsonl'):
                if not (row['checkpointKind']=='FE' and row['checkpoint'] in CHECKS or row['checkpointKind']=='TIME' and row['checkpoint']==read(SOURCE/'protocol.json')['timeSeconds'][stem]):continue
                assert row['bornSeconds']<=row['checkpointElapsedSeconds'] and row['bornFE']<=row['checkpointFE']
                key=tuple(tuple(row[k]) for k in ('JS','FA','MA','WA'))
                reference={'seed':seed,'method':method,'kind':row['checkpointKind'],'checkpoint':row['checkpoint'],
                    'bornFE':row['bornFE'],'bornSeconds':row['bornSeconds']}
                if key not in unique:unique[key]={'case':f'g{len(unique)}','genome':{k:row[k] for k in ('JS','FA','MA','WA','objectives')},'sources':[]}
                assert unique[key]['genome']['objectives']==row['objectives']
                unique[key]['sources'].append(reference)
    cases=list(unique.values());write_once(root/stem/'cases.json',cases)
    lines=[]
    for case in cases:
        g=case['genome'];lines.append('\t'.join([case['case'],','.join(map(str,g['objectives'])),
            *(','.join(map(str,g[k])) for k in ('JS','FA','MA','WA'))]))
    (root/stem/'cases.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return cases


def analyze(root,stem,cases):
    stats={s['case']:s for s in rows(root/stem/'probe/genome-stats.jsonl')};assert len(stats)==len(cases)
    meaningful=[case for case in cases if stats[case['case']]['materialCompatibleMachineWitnesses']>0]
    seeds=sorted({s['seed'] for case in meaningful for s in case['sources']})
    result={'stem':stem,'uniquePaidGenomes':len(cases),'knownSourceRows':sum(len(c['sources']) for c in cases),
        'operations':sum(s['operations'] for s in stats.values()),
        'negativeFirstStageOperations':sum(s['negativeFirstStage'] for s in stats.values()),
        'negativeLaterStageOperations':sum(s['negativeLaterStage'] for s in stats.values()),
        'negativeTerminalOperations':sum(s['negativeMakespanTerminal'] for s in stats.values()),
        'genomesWithFirstStageInversion':sum(s['negativeFirstStage']>0 for s in stats.values()),
        'genomesWithLaterStageInversion':sum(s['negativeLaterStage']>0 for s in stats.values()),
        'maxFirstStageLambda':max(s['maxFirstStageLambda'] for s in stats.values()),
        'maxLambda':max(s['maxLambda'] for s in stats.values()),
        'materialCompatibleMachineGenomes':len(meaningful),'materialSourceSeeds':seeds,
        'worthLegalWitnessProbe':len(meaningful)>=8 and len(seeds)>=2,
        'scope':'Only saved development-front genomes, not incidence in all search attempts. Hypothetical wait previews '
                'are not feasible whole schedules. Compatible first-stage machine previews have no whole-candidate objective evaluation.'}
    write_once(root/stem/'analysis.json',result);return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('fatigue-inversion-audit-%Y%m%d-%H%M%S-%f');root.mkdir();print('FATIGUE_INVERSION_ROOT',root,flush=True)
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            write_once(root/'protocol.json',{'source':str(SOURCE),'instances':STEMS,'seeds':SEEDS,'methods':METHODS,'FECheckpoints':CHECKS,
                'timeCheckpoints':'Actual T4/5seconds','searchFE':0,
                'selection':'All paid objective representatives of the predeclared fronts. Deduplicate exactly by four-vectors '
                            'per instance, retain every seed/method/checkpoint reference, no gain or lambda-based sampling.',
                'engineering':'Full decode and objective bits exact vs paid record, validator, then exact original transition '
                              'replay of every operation. Four analytic derivative fixtures. All offline calls separately counted.',
                'test':'lambda=base*beta*mu*startFatigue; lambda>1+1e-8 indicates negative instantaneous completion derivative. '
                       'Split first/later stage and actual makespan-terminal operations. Hypothetical half-optimal wait '
                       'only verifies local physics and is never inserted in a schedule or search archive.',
                'directControl':'For negative first-stage operations only, preview later-available machines with EXACT same '
                                'speed/power/standby, same worker and prefix. Legal MA encoding exists, but downstream '
                                'schedule and HV unknown. Material local completion decrease>=0.1% of original operation duration.',
                'gate':'Both instances >=8 unique paid genomes with material compatible-machine local witness, covering '
                       '>=2 source seeds. Pass only permits a fresh guarded complete-candidate probe. Failure stops this '
                       'specified delayed-equivalent-machine hypothesis, without adding waiting controls or changing thresholds.',
                'limits':'No new search, beta tuning, adjoint selector, delay genome or decoder rule; no causal explanation '
                         'of NSGA quality gap from frequencies. Zero-FE physics replay is not an online time advantage.'})
            src,classes=root/'source',root/'classes';src.mkdir();classes.mkdir()
            for name in ('FatigueInversionStats','FatigueInversionAudit','ClassResolutionProbe'):
                shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',src)
            shutil.copy2(Path(__file__),src)
            oldcp=(SOURCE/'classpath.txt').read_text('utf-8')
            execute(['javac','-encoding','UTF-8','--release','8','-cp',oldcp,'-d',str(classes),*map(str,src.glob('*.java'))],root/'compile.log')
            write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{oldcp}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
            results=[];receipts=[]
            for stem in STEMS:
                cases=prepare(root,stem);inp=root/stem/'inputs';out=root/stem/'probe'
                cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'research.dynamic.FatigueInversionAudit',str(inp/f'{stem}.txt'),
                    str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(root/stem/'cases.tsv'),str(out)]
                write_once(root/stem/'command.json',cmd);execute(cmd,root/stem/'run.log',timeout=180)
                receipts.append(read(out/'receipt.json'));results.append(analyze(root,stem,cases))
            write_once(root/'analysis.json',{'instances':results,'worthLegalWitnessProbe':all(r['worthLegalWitnessProbe'] for r in results)})
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','searchFE':0,'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'offlineFullDecoderQA':sum(r['offlineFullDecoderQA'] for r in receipts),
        'offlineTransitionPreviews':sum(r['offlineTransitionPreviews'] for r in receipts),
        'worthLegalWitnessProbe':all(r['worthLegalWitnessProbe'] for r in results)})
    print('FATIGUE_INVERSION_COMPLETE',results,flush=True)


if __name__=='__main__':
    main()

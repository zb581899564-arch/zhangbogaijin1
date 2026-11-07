"""No-search physical decomposition of existing paid fronts, plus explicitly offline beta0 counterfactuals."""
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from paired_survival_bench import class_hashes

NAT=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
POP=ROOT/'runs/center-population-probe-20261105-080512-453517'
ARMS=('OFF','FIXED_EA','UNIFORM_EA','TOURNAMENT_EA','NSGA')


def selected_sources(stem):
    for budget in ('FE','TIME'):
        for arm in ('FULL_NAT','NSGA_NAT'):
            folder=NAT/stem/f'{budget}-{arm}'
            for record in rows(folder/'checkpoint-solutions.jsonl'):
                select=(budget=='FE' and record['checkpointKind']=='FE' and record['checkpoint'] in (100,5100,500000)
                        or budget=='TIME' and record['checkpointKind']=='TIME' and record['checkpoint']==(4 if stem.startswith('20_') else 5))
                if select:yield f'NAT/{budget}/{arm}/{record["checkpoint"]}',record
    for seed in (12450003,12450033):
        for arm in ARMS:
            for record in rows(POP/stem/str(seed)/arm/'checkpoint-solutions.jsonl'):
                if record['checkpointKind']=='FE' and record['checkpoint']==5100:
                    yield f'POP/{seed}/{arm}/5100',record


def prepare(root,stem):
    shutil.copytree(NAT/stem/'inputs',root/stem/'inputs');unique={}
    for cohort,record in selected_sources(stem):
        assert record['bornFE']<=record['checkpointFE'] and record['bornSeconds']<=record['checkpointElapsedSeconds']
        key=tuple(tuple(record[k]) for k in ('JS','FA','MA','WA'))
        if key not in unique:unique[key]={'case':f'g{len(unique)}','genome':{k:record[k] for k in ('JS','FA','MA','WA','objectives')},'sources':[]}
        assert unique[key]['genome']['objectives']==record['objectives']
        unique[key]['sources'].append({'cohort':cohort,'bornFE':record['bornFE'],'checkpointFE':record['checkpointFE']})
    cases=list(unique.values());write_once(root/stem/'cases.json',cases)
    lines=[]
    for case in cases:
        g=case['genome'];lines.append('\t'.join([case['case'],','.join(map(str,g['objectives'])),*(','.join(map(str,g[k])) for k in ('JS','FA','MA','WA'))]))
    (root/stem/'cases.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8');return cases


def features(stats):
    stages=stats['stageComponents'];n=stages[0]['operations'];s=len(stages)
    energy=lambda r:r['baseProcessingEnergy']+r['fatigueProcessingEnergy']+r['idleEnergy']
    labor=lambda r:r['baseLabor']+r['fatigueLabor']
    all_energy=sum(map(energy,stages));all_labor=sum(map(labor,stages))
    later=sum(r['operations'] for r in stages[1:]);policy=stats['policyChanges']
    dyn,zero=np.asarray(stats['dynamicObjectives']),np.asarray(stats['beta0Objectives'])
    result={'firstStageEnergyShare':energy(stages[0])/all_energy,'firstStageLaborShare':labor(stages[0])/all_labor,
        'fatigueEnergyShare':sum(r['fatigueProcessingEnergy'] for r in stages)/all_energy,
        'idleEnergyShare':sum(r['idleEnergy'] for r in stages)/all_energy,
        'fatigueLaborShare':sum(r['fatigueLabor'] for r in stages)/all_labor,
        'firstStageFatigueLaborShare':stages[0]['fatigueLabor']/all_labor,
        'laterMachineChangedFraction':sum(policy['machineChangedByStage'][1:])/later,
        'laterWorkerChangedFraction':sum(policy['workerChangedByStage'][1:])/later,
        'laterDispatchRankChangedFraction':sum(policy['dispatchRankChangedByStage'][1:])/later,
        'positiveStartFatigueFraction':sum(r['positiveStartFatigue'] for r in stages)/(n*s),
        'atLeast0p1PctInflationFraction':sum(r['atLeast0p1PctDurationInflation'] for r in stages)/(n*s)}
    result.update({f'beta0FullPolicyRelativeEffect{obj}Pct':float(v) for obj,v in zip(('C','E','W'),100*(dyn/zero-1))})
    return result


def summarize(values):
    return {key:{'median':float(np.median([v[key] for v in values])),
                 'q25':float(np.quantile([v[key] for v in values],.25)),
                 'q75':float(np.quantile([v[key] for v in values],.75)),
                 'minimum':float(min(v[key] for v in values)),
                 'maximum':float(max(v[key] for v in values))} for key in values[0]}


def analyze(root,stem,cases):
    stats={s['case']:s for s in rows(root/stem/'probe/genome-stats.jsonl')};assert len(stats)==len(cases)
    table={case:features(row) for case,row in stats.items()};groups={}
    for case in cases:
        for source in case['sources']:groups.setdefault(source['cohort'],[]).append(table[case['case']])
    result={'stem':stem,'uniquePaidGenomes':len(cases),'sourceRows':sum(len(c['sources']) for c in cases),
        'uniqueGenomeSummary':summarize(list(table.values())),
        'cohorts':{key:{'points':len(v),'summary':summarize(v)} for key,v in groups.items()},
        'limits':'Descriptive saved-front sample; no independence, search-attempt incidence, causal algorithm ranking underbeta0, or new candidate claim.'}
    write_once(root/stem/'analysis.json',result);return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('fatigue-stage-structure-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FATIGUE_STAGE_ROOT',root,flush=True);receipts=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(NAT/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'naturalSource':str(NAT),'populationSource':str(POP),
                'selection':'All paid objective representatives: NAT FULL/NSGA seed12390003 atFE100/5100/500000 andactualT4/5; '
                            'POP5arms*2seeds atFE5100. Exact4vector dedup perinstance, all references retained, no gain/fatigue-based sampling.',
                'question':'Which stages and physical cost components dominate the actually reached fronts, and how much can fatigue change later deterministic decoder events?',
                'physics':'Full dynamic decode must bit-match saved paid objectives and pass validator. '
                          'Perstage E=baseProcessing+fatigueProcessing+idle, W=baseLabor+fatigueLabor, verify closure. '
                          'Beta0 changes only beta, keeping alpha/mu/h0 and current append/FIFO/earliest-resource model. '
                          'Full beta0 decode/validation separately counted; this is samegenome counterfactual, not a beta0 algorithm rerun.',
                'metrics':'Perstage work/exposure/positivefatigue/inflation>=0.1%; firststage shares, fatiguework E/W andidleE; '
                          'later dispatchposition/machine/worker changes perjobstage vsbeta0. Medians/quartiles overuniquegenomes andeachsavedcohort. '
                          'Beta0 effects include downstream reordering/reassignment; directcomponent sums condition on actual dynamic bindings and do not equal counterfactual effects.',
                'decision':'No automatic new algorithm or paid mechanism promotion. Physical firststage binding/order must be exactly unchanged; '
                           'decomposition and everypaid record must validate before interpretation. Descriptive patterns can motivate a distinct separately preregistered hypothesis, '
                           'never relax old gates, filter failed instances, tune beta or resurrect adjoint/delay/commonpool/parentpressure variants.',
                'cost':'0 newsearchFE. Dynamic fullQA andbeta0 fullcounterfactual calls both counted, all operations inspected. '
                       'No offline candidate feedback, model changes, production edits, downloads or transfer.'})
            source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
            for name in ('FatigueStageStats','FatigueStageAudit','ClassResolutionProbe'):
                shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
            shutil.copy2(Path(__file__),source)
            base=(NAT/'classpath.txt').read_text('utf-8')
            execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
            write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
            results=[]
            for spec in specs:
                stem=spec['stem'];cases=prepare(root,stem);inp=root/stem/'inputs';out=root/stem/'probe'
                cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'research.dynamic.FatigueStageAudit',str(inp/f'{stem}.txt'),
                    str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(root/stem/'cases.tsv'),str(out)]
                write_once(root/stem/'command.json',cmd);execute(cmd,root/stem/'run.log',timeout=180)
                receipt=read(out/'receipt.json');assert receipt['status']=='PASS' and receipt['dynamicFullQA']==receipt['beta0OfflineDecodes']==len(cases)
                receipts.append(receipt);results.append(analyze(root,stem,cases))
            write_once(root/'analysis.json',{'instances':results,'searchFE':0,'newAlgorithmProven':False})
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','searchFE':0,'error':repr(error),
            'completedDynamicQA':sum(r['dynamicFullQA'] for r in receipts),'completedBeta0Calls':sum(r['beta0OfflineDecodes'] for r in receipts)});raise
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'dynamicFullQA':sum(r['dynamicFullQA'] for r in receipts),
        'beta0OfflineDecodes':sum(r['beta0OfflineDecodes'] for r in receipts),
        'completedOperationAccounting':sum(r['completedOperationAccounting'] for r in receipts),'newAlgorithmProven':False})
    print('FATIGUE_STAGE_COMPLETE',[(r['stem'],r['uniquePaidGenomes']) for r in results],flush=True)


if __name__=='__main__':main()

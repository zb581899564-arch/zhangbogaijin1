"""Compare separated, joint and fatigue-conditioned remaining bounds on exact paid prefixes."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import json
import shutil
import time
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from paired_survival_bench import class_hashes
from research.reachability.cases import SOURCE
from research.reachability.prefix_cases import make_profiles,analytic_prefix_checks
from research.reachability.prefix_state import fatigue_floor,multiplier
from research.reachability.relaxation import FixedFARelaxation,engineering_checks
from research.reachability.separated_bound import separated_bound

STATIC=ROOT/'runs/fa-reachability-audit-20261105-034607-605907'


def build(root):
    src,classes=root/'source',root/'classes';src.mkdir();classes.mkdir()
    java=ROOT/'src/algorithms/diagnostics/PrefixReachabilityExport.java';shutil.copy2(java,src)
    shutil.copytree(ROOT/'research/reachability',src/'reachability',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(Path(__file__),src)
    cp=(STATIC/'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(src/java.name)],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{cp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


def export(root,cp,spec):
    stem=spec['stem'];folder=root/stem;folder.mkdir();plan=read(STATIC/stem/'cases.json')
    profiles,targets=make_profiles(plan,spec,rows);write_once(folder/'profiles.json',{'profiles':profiles,'targets':targets})
    lines=[]
    for profile in profiles:
        p=profile['point'];lines.append('\t'.join([profile['id'],','.join(map(str,p['objectives'])),
            *(','.join(map(str,p[k])) for k in ('JS','FA','MA','WA'))]))
    path=folder/'profiles.tsv';path.write_text('\n'.join(lines)+'\n',encoding='utf-8');inp=SOURCE/stem/'inputs'
    cmd=['java','-cp',cp,'research.dynamic.PrefixReachabilityExport',str(inp/(stem+'.txt')),
        str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(path),str(folder/'prefixes.jsonl'),str(folder/'prefix-qa.json')]
    write_once(folder/'export-command.json',cmd);execute(cmd,folder/'export.log')
    qa=read(folder/'prefix-qa.json');assert qa['status']=='PASS' and qa['completedProfiles']==len(profiles)
    states={r['id']:r for r in rows(folder/'prefixes.jsonl')}
    metadata=read(STATIC/stem/'physical-coefficients.json');slack=[]
    for p in profiles:
        state=states[p['id']];horizon=p['point']['objectives'][0]
        for op in state['firstStageOperations']:
            if state['completedJobs'][op['job']]:continue
            floor=fatigue_floor(state,metadata,horizon,op['factory'],op['worker'])
            factor=multiplier(state,metadata,horizon,op['factory'],0,op['worker'])
            stage=metadata['factories'][op['factory']][0];pair=op['machine']*stage['workers']+op['worker']
            assert op['u']+1e-12>=floor
            assert op['duration']+1e-9>=stage['base'][op['job']][pair]*factor
            slack.append(op['u']-floor)
    write_once(folder/'floor-physics-check.json',{'status':'PASS','suffixOperationsChecked':len(slack),
        'minimumFatigueSlack':min(slack),'searchFE':0,'extraDecoderCalls':0})
    return profiles,targets,states,metadata,qa


def analyze_instance(root,cp,spec,ledger):
    stem=spec['stem'];profiles,targets,states,metadata,qa=export(root,cp,spec);cache={};requests=[]
    def score(profile,state,target,mode):
        key=(profile['id'],tuple(target),mode)
        if key in cache:return cache[key]
        started=time.monotonic();horizon=target[0] if mode=='FATIGUE' else None
        model=FixedFARelaxation(metadata,profile['assignment'],state,horizon)
        result=model.solve(target);cheap=separated_bound(model,target)
        assert cheap['dual']['lower']<=result['primalMultiplier']+1e-6
        row={'id':len(ledger),'stem':stem,'profile':profile['id'],'method':profile['method'],'seed':profile['seed'],
            'target':target,'mode':mode,'cheap':cheap,**result,'totalScoringSeconds':time.monotonic()-started}
        ledger.append(row)
        with (root/'lp-solves.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        cache[key]=row;return row
    # All witnesses must pass before cross-target information is interpreted.
    for profile in profiles:
        for mode in ('TIME','FATIGUE'):
            assert not score(profile,states[profile['id']],profile['point']['objectives'],mode)['dual']['excludesTarget']
    for profile in profiles:
        state=states[profile['id']]
        for target in targets[profile['seed']]:
            values=target['objectives'];time_bound=score(profile,state,values,'TIME');fatigue_bound=score(profile,state,values,'FATIGUE')
            if np.all(np.asarray(profile['point']['objectives'])<=values):
                assert not time_bound['dual']['excludesTarget'] and not fatigue_bound['dual']['excludesTarget']
            requests.append({'profile':profile['id'],'method':profile['method'],'seed':profile['seed'],'targetLabels':target['labels'],
                'timeSolve':time_bound['id'],'fatigueSolve':fatigue_bound['id'],
                'cheapTimeExcludes':time_bound['cheap']['dual']['excludesTarget'],'timeLPExcludes':time_bound['dual']['excludesTarget'],
                'cheapFatigueExcludes':fatigue_bound['cheap']['dual']['excludesTarget'],'fatigueLPExcludes':fatigue_bound['dual']['excludesTarget']})
    summary=[]
    for seed in read(STATIC/'protocol.json')['seeds']:
        current=[r for r in requests if r['seed']==seed and r['method']=='STRICT_FULL']
        joint=sum(r['timeLPExcludes'] and not r['cheapTimeExcludes'] for r in current)
        unique=sum(r['fatigueLPExcludes'] and not r['timeLPExcludes'] and not r['cheapFatigueExcludes'] for r in current)
        summary.append({'seed':seed,'requests':len(current),'jointOnly':joint,'fatigueJointOnly':unique,
            'jointOnlyFraction':joint/len(current),'fatigueJointOnlyFraction':unique/len(current)})
    result={'stem':stem,'summary':summary,'requests':requests,'prefixQA':qa,
        'ordinaryJointInformationSupported':sum(r['jointOnlyFraction']>=.2 for r in summary)>=2,
        'fatigueJointInformationSupported':sum(r['fatigueJointOnlyFraction']>=.1 for r in summary)>=2}
    write_once(root/stem/'analysis.json',result)
    print('PREFIX_REACHABILITY_INSTANCE',stem,summary,flush=True);return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('prefix-reachability-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('PREFIX_REACHABILITY_ROOT',root,flush=True);ledger=[];started=time.monotonic()
    (root/'lp-solves.jsonl').touch(exist_ok=False)
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(STATIC/'protocol.json')['instances']
            write_once(root/'protocol.json',{'source':str(STATIC),'instances':specs,'prefix':'First floor(N/2) entries in each paid full JS; only stage0 committed. Later stages can reorder and are entirely relaxed.',
                'physics':'Export exact DynamicPrefix stage0 state. Full and constructed-prefix decoding must have identical complete timeline and old objectives. Check fatigue floor against every uncommitted stage0 operation in its known full completion.',
                'bounds':'CHEAP: maximum separated objective/job-chain/uniform-machine/uniform-worker dual bound. TIME_LP: jointly allocate fractional remaining operations with fixed past energy/labor, stage0 resource availability and committed job readiness. FATIGUE_LP: same plus u>=h_last*exp(-mu*(Ctarget-end_last)) for stage0 remaining workers, rounded down with1e-10 allowance. Later-stage fatigue stays relaxed.',
                'duals':'Nonzero prefix constants contribute priced committed cost/time to the dual bound. Price mass upper enclosure and60-digit downward verification used; target budgets inflate1e-10 and exclusion requires lower>1.000001. Solver multipliers are not true dynamic optimum predictions.',
                'controls':'All saved MAIN and NSGA representative prefixes; same own/cross target sets and costs. MAIN prefixes are primary for information gate. Never charge a copied paid point as a new discovery. A good Pareto prefix can legitimately fail to dominate other Pareto targets.',
                'engineering':'Four original closed-form LP cases plus analytic prefix case where separated past/time feasibility lacks future fatigue and exact fatigue makes joint target impossible. All chosen own completions and any known weakly dominating cross completions must not be excluded.',
                'gates':'Per instance >=2/3 seeds: ordinary joint-only exclusion>=20% of registered MAIN prefix-target pairs over CHEAP_TIME; fatigue-joint-only exclusion>=10% over BOTH TIME_LP and CHEAP_FATIGUE. Both instances required for a common information hypothesis. These are information gates only, not candidate quality, local regret, four-role value or algorithm efficacy.',
                'cost':'Zero new searchFE. Every offline full/constructed decoding and prefix-append transition counted. LP solves, preparation, separated scoring and Decimal verification timed; no online or same-time performance claim. No new selector, Q changes, model change or public upload.',
                'scope':'Old two development instances/three seeds and pre-fixed representatives. No new algorithm seed, independent test, uniqueness claim or original-author reproduction.'})
            checks=engineering_checks()+analytic_prefix_checks();write_once(root/'engineering-checks.json',{'status':'PASS','LPCalls':len(checks),'checks':checks,'searchFE':0,'decoderCalls':0})
            cp=build(root);results=[analyze_instance(root,cp,s,ledger) for s in specs]
            result={'instances':[{k:v for k,v in r.items() if k!='requests'} for r in results],
                'ordinaryJointInformationSupported':all(r['ordinaryJointInformationSupported'] for r in results),
                'fatigueJointInformationSupported':all(r['fatigueJointInformationSupported'] for r in results),
                'uniqueLPSolves':len(ledger),'engineeringLPCalls':len(checks),'searchFE':0,
                'offlineFullDecodes':sum(r['prefixQA']['successfulFullDecodes'] for r in results),
                'prefixAppendTransitions':sum(r['prefixQA']['prefixAppendTransitions'] for r in results)}
            write_once(root/'analysis.json',result)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','LPCallsCompleted':len(ledger),'error':str(exc),'searchFE':0});raise
    write_once(root/'status.json',{'status':'COMPLETE',**{k:v for k,v in result.items() if k!='instances'},'wallSeconds':time.monotonic()-started})
    print('PREFIX_REACHABILITY_COMPLETE',{k:v for k,v in result.items() if k!='instances'},flush=True)


if __name__=='__main__':main()

"""Input-only linear assignment relaxation, explicitly separated from actual dynamic candidate quality."""
from datetime import datetime
from pathlib import Path
import shutil
import time
import numpy as np
import scipy
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from paired_survival_bench import class_hashes
from factory_affinity_math import checks,value,exact,swap_descent,cycles

SOURCE=ROOT/'runs/global-working-audit-20261105-055724-963327'
PHYSICS=ROOT/'runs/fatigue-stage-structure-20261105-081926-044334'
NAT=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
SEEDS=(11730007,11730037)
RANGES={'MAKESPAN':(0,15),'CENTER':(15,70),'ENERGY':(70,85),'WORKER_COST':(85,100)}


def parents(stem):
    result=[]
    for seed in SEEDS:
        for snap in rows(SOURCE/stem/str(seed)/'ON/global-working-pools.jsonl'):
            if snap['step'] not in (24,49):continue
            role=snap['role'];lo,hi=RANGES[role]
            assert hi-lo==snap['roleParentCount'] and snap['parentCount']==100
            free=[p for p in snap['points'][lo:hi] if p['category']==0]
            assert len(free)==(47 if role=='CENTER' else 11)
            for position in np.linspace(0,len(free)-1,8,dtype=int):
                p=free[position];fa=np.empty(len(p['JS']),dtype=int);fa[p['JS']]=p['FA']
                assert p['earliestKnownPaidFE']<=snap['paidFE'] and np.all(np.bincount(fa,minlength=int(stem.split('_')[2]))>0)
                result.append({'seed':seed,'role':role,'step':snap['step'],'freeIndex':int(position),
                    'sourcePaidFE':snap['paidFE'],'sourceGenome':p,'factoryByJob':fa.tolist()})
    assert len(result)==128
    return result


def costs(data):
    result={}
    for label,key in (('ENERGY','stageBaseEnergyMin'),('WORKER_COST','stageBaseLaborMin')):
        values=np.empty((data['jobs'],data['factories'],data['stages']))
        for item in data['data']:values[item['job'],item['factory']]=item[key]
        result[label]=(values.sum(axis=2),values[:,:,0])
    return result


def analyze(root,stem,cases):
    matrices=costs(read(root/stem/'affinity-inputs.json'));observations=[]
    for case_id,case in enumerate(cases):
        initial=np.asarray(case['factoryByJob'],dtype=int)
        for label,(allstage,firststage) in matrices.items():
            start=time.perf_counter();local,steps,residual=swap_descent(allstage,initial)
            local_time=time.perf_counter()-start
            start=time.perf_counter();optimal=exact(allstage,initial);exact_time=time.perf_counter()-start
            first=exact(firststage,initial);base,after,best=(value(allstage,a) for a in (initial,local,optimal))
            assert best<=after+1e-8*max(1,after) and after<=base+1e-8*max(1,base)
            cycle=cycles(allstage,local,optimal);gain=100*(after-best)/after
            if gain>=.2:assert any(len(c['jobs'])>=3 and c['delta']<0 for c in cycle)
            observations.append({'case':case_id,'seed':case['seed'],'role':case['role'],'step':case['step'],'costModel':label,
                'originalRelaxation':base,'twoSwapLocalRelaxation':after,'exactRelaxation':best,
                'exactGainOverOriginalPct':100*(base-best)/base,'extraBeyondTwoSwapPct':gain,
                'firstStageOptimalScoredAllStages':value(allstage,first),
                'allStageAdvantageVsFirstStageProxyPct':100*(value(allstage,first)-best)/best,
                'twoSwapSteps':steps,'minimumResidualPairDelta':residual,
                'twoSwapFactoryByJob':local.tolist(),'exactFactoryByJob':optimal.tolist(),'cyclesFromTwoSwapToExact':cycle,
                'swapSeconds':local_time,'exactSeconds':exact_time})
    material=[r for r in observations if r['extraBeyondTwoSwapPct']>=.2]
    supported=len(material)>=.2*len(observations) and len({r['role'] for r in material})>=2 and len({r['seed'] for r in material})==2
    summary={}
    for label in matrices:
        own=[r for r in observations if r['costModel']==label]
        summary[label]={'cases':len(own),'materialBeyondTwoSwap':sum(r['extraBeyondTwoSwapPct']>=.2 for r in own),
            'medianExtraBeyondTwoSwapPct':float(np.median([r['extraBeyondTwoSwapPct'] for r in own])),
            'maxExtraBeyondTwoSwapPct':float(max(r['extraBeyondTwoSwapPct'] for r in own)),
            'medianGainVsOriginalPct':float(np.median([r['exactGainOverOriginalPct'] for r in own])),
            'medianAllStageVsFirstStageProxyPct':float(np.median([r['allStageAdvantageVsFirstStageProxyPct'] for r in own]))}
    result={'stem':stem,'summary':summary,'costCases':len(observations),'materialCases':len(material),
        'rolesWithMaterialGap':sorted({r['role'] for r in material}),'seedsWithMaterialGap':sorted({r['seed'] for r in material}),
        'relaxationGate':bool(supported),'observations':observations,
        'scope':'Independent per-operation resource minima and fixed factory job counts. No actual candidate decode, fatigue timing prediction, feasible objective improvement, role-sharing benefit or novelty claim.'}
    write_once(root/stem/'analysis.json',result);return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('factory-affinity-assignment-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FACTORY_AFFINITY_ROOT',root,flush=True)
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(NAT/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'parentSource':str(SOURCE),'physicalMotivation':str(PHYSICS),
                'sampling':'2existinginstances, source11730007/37, all4roles atglobalstep24/49, 8equidistantfreeparents percontext. '
                           '128parents perinstance, no gain-based sampling/replacement. Labels and actualpaidprovenance retained.',
                'relaxation':'Perjobfactory sum over ALL stages of minimum baseE or baseW across legalmachine/worker pairs. '
                             'Independent minima perobjective, no claim jointlyrealizableresources. Fatigue/idle/order ignored. '
                             'Keep eachparent factoryjobcounts exact; optimize byduplicatedslotlinearassignment. '
                             'Compare original, complete deterministic steepest2job-swap descent toconvergence, exactglobalassignment and firststage-only exactproxy.',
                'question':'Is there material all-stage allocation opportunity BEYOND ordinary pair-exchange closure, rather than merely another heuristic for already covered swaps?',
                'gate':'Eachinstance >=20%of256costcases exact beats2swaplocal by>=0.2%oflocalrelaxationcost, covering>=2source roles andbothsource seeds. '
                       'Allnecessary to retain global-cycle hypothesis; failure stops this static-capacity-preserving allocation mechanism without changedquota, costweights, sourcewindows or seeds. '
                       'Pass only allows design of a separate actual legal dynamic candidate probe; boundgain is not true objective gain.',
                'engineering':'16N6/F3 fixedquota instances exactchecked againstall90assignments; explicit3cycle fixture hidden fromallpairs. '
                              'Allsourceparents free andpaid; actual counts/feasibility preserved. Negative closed assignment trails retained.',
                'limits':'This is a zeroDecoder offline mathematical diagnostic, not new fullalgorithm or beta0 search. '
                         'Earlier fixedFA LP target-exclusion failed; here FA changes under fixedcounts and the primarycontrol is pair-swapclosure. '
                         'Do not infer novel fatigue-specific complementarity from static algebra or promote ordinarycontrol after failure.',
                'runtime':{'scipy':scipy.__version__},'preserved':'0searchFE/0decoder calls, no candidate fedback, production/model/Q/family/sharedrule unchanged; no download/transfer.'})
            write_once(root/'mathematics-checks.json',checks())
            source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
            for name in ('FactoryAffinityInputs','ClassResolutionProbe'):
                shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
            for name in ('audit_factory_affinity_assignment.py','factory_affinity_math.py'):
                shutil.copy2(Path(__file__).with_name(name),source)
            base=(NAT/'classpath.txt').read_text('utf-8')
            execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
            write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
            results=[]
            for spec in specs:
                stem=spec['stem'];shutil.copytree(NAT/stem/'inputs',root/stem/'inputs');inp=root/stem/'inputs'
                cases=parents(stem);write_once(root/stem/'parents.json',cases)
                cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'research.dynamic.FactoryAffinityInputs',str(inp/f'{stem}.txt'),
                     str(inp/'RECONSTRUCTED-setup.txt'),str(root/stem/'affinity-inputs.json')]
                write_once(root/stem/'command.json',cmd);execute(cmd,root/stem/'run.log');results.append(analyze(root,stem,cases))
            write_once(root/'analysis.json',{'instances':results,'retainGlobalCycleHypothesis':all(r['relaxationGate'] for r in results),'searchFE':0,'decoderCalls':0})
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','searchFE':0,'decoderCalls':0,'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'decoderCalls':0,'parents':256,'costCases':512,
        'retainGlobalCycleHypothesis':all(r['relaxationGate'] for r in results)})
    print('FACTORY_AFFINITY_COMPLETE',[(r['stem'],r['materialCases'],r['relaxationGate'],r['summary']) for r in results],flush=True)


if __name__=='__main__':main()

"""One newseed, identical model and algorithm parameters; only natural versus fixed local-budget regimes."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from run_dynamic_deep_roles import ledger
from run_center_entry_cross_replay import write_ledger
from paired_survival_bench import ANCHOR
from natural_local_support import run_case
from natural_regime_analysis import analyze

ENTRY=ROOT/'runs/natural-local-audit-20261105-073204-330248'
SEED=12390003;STEMS=('20_8_5_1','100_2_3_1')
METHODS={'FULL_NAT':('STRICT_FULL','record'),'FULL_REPLAY':('STRICT_FULL','replay'),
         'NSGA_NAT':('NSGA_STRICT','record'),'NSGA_REPLAY':('NSGA_STRICT','replay'),
         'LI_NAT':('LI_STRICT','record'),'SYNC_NAT':('COST_SYNC','record'),
         'UNIFORM_NAT':('COST_UNIFORM','record'),'SHARE_BASE_NAT':('FORCE_STRICT','record')}


def execution_order():
    cases=[];labels=list(METHODS)
    for b,budget in enumerate(('FE','TIME')):
        for i,stem in enumerate(STEMS):
            offset=(i*3+b*5)%len(labels)
            for label in labels[offset:]+labels[:offset]:cases.append({'stem':stem,'budget':budget,'method':label})
    return cases


def paired_acceptance(root,stem):
    initial=[]
    for method in METHODS:
        for budget in ('FE','TIME'):
            folder=root/stem/f'{budget}-{method}'
            if not (folder/'accounting-acceptance.json').exists():continue
            data=rows(folder/'initial-population.jsonl');assert len(data)==100,'Registered time did not permit common initialization'
            initial.append(data)
        folders=[root/stem/f'{b}-{method}' for b in ('FE','TIME')]
        if all((f/'accounting-acceptance.json').exists() for f in folders):
            fronts=[{r['checkpoint']:r['front'] for r in rows(f/'anytime.jsonl') if r['checkpointKind']=='FE' and r['reached']} for f in folders]
            assert all(fronts[0][key]==fronts[1][key] for key in fronts[0].keys()&fronts[1].keys())
    assert all(data==initial[0] for data in initial)
    for budget in ('FE','TIME'):
        for family in ('FULL','NSGA'):
            folders=[root/stem/f'{budget}-{family}_{regime}' for regime in ('NAT','REPLAY')]
            if not all((f/'accounting-acceptance.json').exists() for f in folders):continue
            fronts=[{r['checkpoint']:r['front'] for r in rows(f/'anytime.jsonl') if r['checkpointKind']=='FE' and r['reached']} for f in folders]
            assert all(fronts[0][key]==fronts[1][key] for key in (1,2,100,5100) if key in fronts[0] and key in fronts[1]),'Regime changed pre-local front'


def main():
    assert read(ENTRY/'status.json')['naturalEntryAccepted']
    root=ROOT/'runs'/datetime.now().strftime('natural-regime-bench-%Y%m%d-%H%M%S-%f');root.mkdir();print('NATURAL_REGIME_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(ROOT/'runs/makespan-tie-screen-20261105-025223-471920/protocol.json')['instances'];order=execution_order()
            write_once(root/'protocol.json',{'entrySource':str(ENTRY),'instances':specs,'seed':SEED,'methods':METHODS,'order':order,
                'plannedFixedSuccessfulFE':8000000,'fixedFELimit':500000,'plannedTrueTimeSeconds':72,'timeSafetyFECap':500000,
                'question':'Does the latest four-role search become competitive under its original state-dependent natural VNS stopping rather than an inherited fixed local-quota ledger?',
                'changed':'NAT uses existingrecordmode: randomfactory, VNSnaturalreturn, unchangedouter rounds. No forced fill-quota restarts. '
                          'REPLAY keeps20_2template visit/group/round/paid and independent factory draws as before. No CRITICAL routing or failed mechanism.',
                'controls':'FULL_NAT/FULL_REPLAY,NSGA_NAT/NSGA_REPLAY isolate regime withinalgorithm;LI_NAT isv2reconstruction+commonnaturaldeepLS, '
                           'not originalpublished algorithm. SYNC/UNIFORM/SHARE_BASE use same accepted settings except explicit ablations. '
                           'All table templates forcedSTRICTM,OLDESTmemory,ANCHORcopy; identical initial100vectors/physical input perseed.',
                'budget':'Separate exact500kFE and actualTIME_LIMIT4/5s perinstance, oneJVM atatime. Natural variants share LS rules but may '
                         'spend different stage fees and complete different numbers of visits. All attempts/duplicates/cache/archive/capture charged; fullcheckpointQA separate.',
                'metrics':'PrimaryHV1.5, sensitivity1.25/2, originalnumericnormalization. IGD+ perinstance/budget empiricalNDunionofall8arms, nosearchfeedback. '
                          'Report stagefees, localvisits/slots/restarts, rawgenerationcounter definitions, extremeobjectives and capped/missingcoverage.',
                'gate':'Bothinstances and BOTHbudgets FULL_NAT vsNSGA_NAT>=-1%HV; vsLI_NAT andSHARE_BASE_NAT>=+1%; '
                       'vsFULL_REPLAY>=+1%. Ref1.25/2 nonnegative vsLi/base/oldregime and>=-2%vsNSGA. '
                       'IGD+ symmetricworsening<=5%vsall4. Fourduties vsUNIFORM_NAT>=+1%bothbudgets/instances; '
                       'sharing vsSYNC_NAT>=-0.5%everycase and>=+0.2%atleastone. Allforfreshseed-screen only. '
                       'Failure retained; no changingT/seed/localrounds or choosingonly a winningbudget/instance.',
                'limits':'One newseed on repeateddevelopmentinstances, not independent confirmation or an innovative newalgorithm. '
                         'No causal attribution to role alone when naturalallocation differs; older ledger-conditioned evidence not overwritten.',
                'preserved':'No default production, oldinput/source/records, Q/operator, roles/family/shared rule changes; no downloads/transfers/push.'})
            for name in ('run_natural_regime_bench.py','natural_regime_analysis.py','natural_local_support.py'):
                shutil.copy2(Path(__file__).with_name(name),root/name)
            cp=(ENTRY/'classpath.txt').read_text('utf-8');(root/'classpath.txt').write_text(cp,encoding='utf-8')
            for stem in STEMS:
                shutil.copytree(ENTRY/stem/'inputs',root/stem/'inputs');factories=int(stem.split('_')[2]);rng=np.random.default_rng(SEED^0x5A17)
                slots=[(v,g,r,int(rng.integers(factories)) if r>=0 else -1,paid,0) for v,g,r,f,paid,restarts in ledger(ANCHOR/'SPECIAL-LINEAR')]
                write_ledger(root/stem/'ledger.csv',slots)
            for case in order:
                stem,method,budget=(case[k] for k in ('stem','method','budget'));template,regime=METHODS[method]
                seconds=float('inf') if budget=='FE' else next(s['time_seconds'] for s in specs if s['stem']==stem)
                out,receipt=run_case(root,cp,stem,f'{budget}-{method}',template,regime,SEED,seconds=seconds,ledger=root/stem/'ledger.csv')
                completed.append((out,receipt));paired_acceptance(root,stem)
            result=analyze(root,specs)
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),
            'successfulFECompleted':sum(r['successful'] for _,r in completed),'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','runs':len(completed),'successfulFE':sum(r['successful'] for _,r in completed),
        'attemptedFE':sum(r['attempted'] for _,r in completed),'timeInterruptedAttempts':sum(r['timeInterruptedAttempts'] for _,r in completed),
        'unexpectedEvaluationFailures':0,'checkpointFullDecoderQA':sum(read(out/'checkpoint-validation.json')['uniqueOfflineDecodes'] for out,_ in completed),
        'worthFreshSeedScreen':result['worthFreshSeedScreen']})
    print('NATURAL_REGIME_COMPLETE',[(r['stem'],r['efficacyGate'],r['fourDutyGate']) for r in result['instances']],flush=True)


if __name__=='__main__':main()

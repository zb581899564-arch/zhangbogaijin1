"""Counterbalanced observer-off cost validation of the already-equivalent shared snapshot helper."""
from datetime import datetime
from pathlib import Path
import shutil
import time
import numpy as np
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_snapshot_anchor_audit import SOURCE, STEMS, METHODS, SEED, override
from run_frozen_cost_profile import verify_trace

ENGINEERING = ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
REPEATS = 3


def order():
    result=[]
    for rep in range(REPEATS):
        for s,stem in enumerate(STEMS):
            methods=METHODS if (rep+s)%2==0 else METHODS[::-1]
            for method in methods:
                modes=('SERIAL','ANCHOR') if (rep+s+METHODS.index(method))%2==0 else ('ANCHOR','SERIAL')
                result.extend({'stem':stem,'method':method,'rep':rep,'mode':mode} for mode in modes)
    return result


def run_case(root,cp,case):
    stem,method,rep,mode=(case[k] for k in ('stem','method','rep','mode'))
    original=SOURCE/stem/str(SEED)/method
    out=root/stem/method/f'repeat-{rep}'/mode;out.mkdir(parents=True)
    cmd=read(original/'command.json');entry=cmd.index('research.dynamic.PddrIsolationRun')
    cmd[cmd.index('-cp')+1]=cp
    for index,name in ((1,f'{stem}.txt'),(2,'RECONSTRUCTED-setup.txt'),(3,'fatigue-input.txt')):
        cmd[entry+index]=str(root/stem/'inputs'/name)
    cmd[entry+4]=str(out);cmd[entry+7]=str(root/stem/'ledger.csv')
    cmd=override(cmd,'research.snapshot.mode',mode)
    cmd=override(cmd,'research.snapshot.audit','false')
    cmd=override(cmd,'research.memory.audit','false')
    write_once(out/'command.json',cmd)
    print('SNAPSHOT_COST',stem,method,rep,mode,flush=True)
    start=time.monotonic();execute(cmd,out/'run.log',timeout=240);wall=time.monotonic()-start
    receipt=verify_trace(out,original);metrics,=rows(out/'copy-metrics.jsonl')
    assert not metrics['enabled'] and receipt['paidSHA256'] is None
    process={'processSeconds':wall,'searchSeconds':receipt['searchSeconds'],
             'successfulFE':receipt['successful'],'offlineReturnQA':read(out/'summary.json')['offlineValidationDecodes']}
    write_once(out/'process.json',process)
    return {**case,**process}


def analyze(root,cases):
    cells=[]
    for stem in STEMS:
        for method in METHODS:
            pairs=[]
            for rep in range(REPEATS):
                matched={c['mode']:c for c in cases if c['stem']==stem and c['method']==method and c['rep']==rep}
                pairs.append({'rep':rep,'serialSearchSeconds':matched['SERIAL']['searchSeconds'],
                    'anchorSearchSeconds':matched['ANCHOR']['searchSeconds'],
                    'speedup':matched['SERIAL']['searchSeconds']/matched['ANCHOR']['searchSeconds']})
            cells.append({'stem':stem,'method':method,'pairs':pairs,
                'medianSpeedup':float(np.median([p['speedup'] for p in pairs]))})
    methods=[]
    for method in METHODS:
        selected=[c for c in cells if c['method']==method]
        median=float(np.median([p['speedup'] for c in selected for p in c['pairs']]))
        passed=median>=1.05 and all(c['medianSpeedup']>=.98 for c in selected)
        methods.append({'method':method,'medianSpeedupAcrossSixPairs':median,'costGate':bool(passed)})
    result={'cells':cells,'methods':methods,'sharedCostGate':all(m['costGate'] for m in methods),
        'scope':'Three counterbalanced repeats of identical development trajectories, not new statistical seeds, '
                'a change in same-FE quality, actual TIME_LIMIT performance, or a paper algorithm contribution.'}
    write_once(root/'analysis.json',result)
    return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('snapshot-cost-bench-%Y%m%d-%H%M%S-%f')
    root.mkdir();print('SNAPSHOT_COST_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            assert read(ENGINEERING/'status.json')['wholeTraceEngineeringAccepted']
            cases=order()
            write_once(root/'protocol.json',{
                'engineeringSource':str(ENGINEERING),'trajectorySource':str(SOURCE),'seed':SEED,'repeats':REPEATS,
                'instances':STEMS,'methods':METHODS,'order':cases,'plannedSuccessfulFE':12000000,
                'measurement':'Separate JVM per run, unchangedXms32m/Xmx2g. Both paid digest and copy timing disabled. '
                              'Same500000FE trajectory, physics, initial vectors, physical ledger and source kernel. '
                              'Methods and snapshot mode pair orders counterbalanced before results.',
                'acceptance':'All24 runs500000successful/0failed and reproduce frozen FE fronts, final genomes, initial '
                             'population, ledger, search counts and decoder operations; metrics disabled.',
                'costGate':'For EACH algorithm median speedup across its6 pairs>=1.05, no per-instance3-repeat median '
                           'speedup<0.98. All required for shared-cost promotion; failure does not trigger extra repeats.',
                'next':'Only a shared cost pass allows a separate trueTIME_LIMIT comparison. Even a speed pass cannot '
                       'promote unchanged same-FE algorithm quality or substitute for scientific contribution gates.',
                'preserved':'No production changes, no new operator/learning/sharing selector/cap, no external transfer.'})
            shutil.copy2(Path(__file__),root/Path(__file__).name)
            cp=(ENGINEERING/'classpath.txt').read_text('utf-8')
            (root/'classpath.txt').write_text(cp,encoding='utf-8')
            for stem in STEMS:
                shutil.copytree(ENGINEERING/stem/'inputs',root/stem/'inputs')
                shutil.copy2(ENGINEERING/stem/'ledger.csv',root/stem/'ledger.csv')
            for case in cases:completed.append(run_case(root,cp,case))
            result=analyze(root,completed)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(c['successfulFE'] for c in completed),
        'failedFE':0,'offlineReturnFullDecoderQA':sum(c['offlineReturnQA'] for c in completed),
        'sharedCostGate':result['sharedCostGate']})
    print('SNAPSHOT_COST_COMPLETE',result['methods'],flush=True)


if __name__=='__main__':
    main()

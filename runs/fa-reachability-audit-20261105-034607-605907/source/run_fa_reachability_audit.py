"""Offline necessary-condition audit using fixed FA and already-paid three-objective targets."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import json
import shutil
import time
import numpy as np
import scipy

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from paired_survival_bench import class_hashes
from research.reachability.cases import SOURCE,prepare
from research.reachability.relaxation import FixedFARelaxation

STEMS=('20_8_5_1','100_2_3_1')
SEEDS=(10950003,10950033,10950063)
BASIS=ROOT/'runs/final-survival-audit-20261105-031556-115852'


def build(root):
    src,classes=root/'source',root/'classes';src.mkdir();classes.mkdir()
    for name in ('ReachabilityInstanceExport','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',src)
    shutil.copytree(ROOT/'research/reachability',src/'reachability',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(Path(__file__),src)
    cp=(BASIS/'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),*map(str,src.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{cp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


class Audit:
    def __init__(self,root):
        self.root=root;self.records=[];self.models={};self.solved={}
        self.log=(root/'lp-solves.jsonl').open('x',encoding='utf-8')

    def solve(self,stem,metadata,fa,target,label):
        key=(stem,tuple(fa),tuple(target))
        if key in self.solved:return self.solved[key]
        modelkey=key[:2]
        if modelkey not in self.models:self.models[modelkey]=FixedFARelaxation(metadata,fa)
        value=self.models[modelkey].solve(target)
        row={'id':len(self.records),'stem':stem,'assignment':list(fa),'target':list(target),'firstRequestedBy':label,**value}
        self.records.append(row);self.log.write(json.dumps(row,ensure_ascii=False)+'\n');self.log.flush()
        self.solved[key]=row;return row

    def instance(self,spec,cp):
        stem=spec['stem'];folder=self.root/stem;folder.mkdir();inp=SOURCE/stem/'inputs'
        cmd=['java','-cp',cp,'research.dynamic.ReachabilityInstanceExport',str(inp/(stem+'.txt')),
            str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(folder/'physical-coefficients.json')]
        write_once(folder/'export-command.json',cmd);execute(cmd,folder/'export.log')
        metadata=read(folder/'physical-coefficients.json');assert metadata['decoderCalls']==metadata['candidateEvaluations']==0
        plan=prepare(spec,SEEDS,read,rows);write_once(folder/'cases.json',plan)
        # Verify every chosen known feasible point first, before interpreting any exclusion.
        checks=[]
        for cohort in plan['cohorts']:
            for check in cohort['selfChecks']:
                result=self.solve(stem,metadata,check['assignment'],check['objectives'],'KNOWN_FEASIBLE_SELF')
                assert not result['dual']['excludesTarget'],(stem,cohort['seed'],check,result)
                checks.append({'seed':cohort['seed'],'kind':check['kind'],'solveId':result['id']})
        write_once(folder/'known-feasible-checks.json',{'status':'PASS','checks':checks,'decoderCalls':0})
        summary=[]
        for cohort in plan['cohorts']:
            target_results=[]
            for target in cohort['targets']:
                tests=[]
                for anchor in cohort['anchors']:
                    result=self.solve(stem,metadata,anchor['assignment'],target['objectives'],'CROSS_FA_TARGET')
                    tests.append({'anchorLabels':anchor['labels'],'solveId':result['id'],
                        'lower':result['dual']['lower'],'excludes':result['dual']['excludesTarget']})
                family=[t for t in tests if any(s.startswith('fixedFamily') for s in t['anchorLabels'])]
                target_results.append({'labels':target['labels'],'target':target['objectives'],'tests':tests,
                    'allSelectedFAsExcluded':all(t['excludes'] for t in tests),
                    'allFixedFamiliesExcluded':all(t['excludes'] for t in family)})
            summary.append({'seed':cohort['seed'],'selectedUniqueFAs':len(cohort['anchors']),'targets':target_results,
                'allSelectedExcludedFraction':float(np.mean([t['allSelectedFAsExcluded'] for t in target_results])),
                'allFixedExcludedFraction':float(np.mean([t['allFixedFamiliesExcluded'] for t in target_results]))})
            print('FA_REACHABILITY_COHORT',stem,cohort['seed'],'FA',len(cohort['anchors']),'targets',len(target_results),
                'allExcluded',summary[-1]['allSelectedExcludedFraction'],flush=True)
        result={'stem':stem,'cohorts':summary,'knownFeasibleChecks':len(checks),'initialFatigueAllZero':not metadata['anyInitialFatigue'],
            'commonFAObstructionSupported':sum(c['allSelectedExcludedFraction']>=.5 for c in summary)>=2,
            'scope':'Each exclusion concerns the recorded fixed assignment and target only. Non-exclusion does not prove the target reachable; selected assignments do not exhaust all available or possible FA.'}
        write_once(folder/'analysis.json',result);return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('fa-reachability-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FA_REACHABILITY_ROOT',root,flush=True);audit=Audit(root);start=time.monotonic()
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=[s for s in read(SOURCE/'protocol.json')['instances'] if s['stem'] in STEMS]
            write_once(root/'protocol.json',{'instances':specs,'seeds':SEEDS,'source':str(SOURCE),'scipyVersion':scipy.__version__,
                'scope':'Offline conditional reachability diagnosis on old development results, not new optimizer seeds, a performance screen or proof of optimality.',
                'relaxation':'For each job/stage choose fractional machine-worker assignments within its fixed factory. Minimize common normalized capacity/cost multiplier t. Resource workloads and each job chain <=t*Ctarget; energy<=t*Etarget; labor<=t*Wtarget. Ignore fatigue, resource/flow order, nonpreemption and nonnegative standby. Thus every feasible target schedule implies a relaxed feasible point with t<=1 up to conservative numerical margins.',
                'coefficients':'Export actual loaded DynamicPhysics arithmetic (p/speed+setup)/efficiency, power*base and wage*base from cached JDK/input/SUT. Round coefficients down3ULP and inflate all target budgets by1e-10 to cover positive floating accumulation in these bounded instances. No static Instance.duration substitute or model change.',
                'dualCertificate':'Use nonnegative prices=-inequality marginals, clip numerical negatives and normalize mass<=1 with60-digit downward Decimal arithmetic. Sum over job/stage groups the minimum priced alternative gives a feasible dual lower bound. Accept numerical exclusion only when independently reconstructed lower>1.000001, not from solver infeasibility/status alone.',
                'preflight':'Four already executed analytic zero-decoder fixtures: one job1, tight time2, parallel capacity1, joint time/energy10/9; primal and reconstructed dual agree within1e-7. Local test execution preceded this descriptive protocol. Exact executable fixtures retained in source.',
                'realEngineering':'Before cross-target interpretation, all selected known feasible MAIN and NSGA points must satisfy lower<=1.000001 under their own assignment. Failure stops the engineering layer. Solver error/limit retained, not called infeasibility.',
                'selection':'Per instance fixed shared Cmax quartile cuts from prior regional audit. Per seed targets are NSGA minima of each objective and nearest three common quartile points, deduplicated. FA anchors are four initial protected families plus MAIN representatives under the same six selectors, deduplicated. No source or target benefit resampling.',
                'gate':'Common FA obstruction requires >=50% selected NSGA targets excluded under every selected MAIN/family FA in >=2/3 seeds on each instance. Local exclusions may still be reported narrowly. Failure does not certify FA adequacy and does not authorize a search rule.',
                'fatigueBoundary':'Initial h0 is exported. When all h0=0, the simple initial-fatigue decay floor is identically zero and is not run as a different informative method. Any stronger prefix-conditioned fatigue bound requires its own derivation and validation.',
                'cost':'Zero new searchFE and zero decoder calls; all LP preparation/solves and Decimal verification timed and counted. Reuse previously paid/validated schedules, never add relaxation solutions to any result archive. CPU solver threads1; no downloads or installations.',
                'limits':'Relaxed feasibility and fractional assignments are not actual schedules. Positive certificates are conditional on FA; they do not prove an algorithm cause, four-duty novelty, time advantage or original-author reproduction.'})
            cp=build(root);results=[audit.instance(s,cp) for s in specs]
            summary={'instances':results,'commonFAObstructionSupported':all(r['commonFAObstructionSupported'] for r in results),
                'searchFE':0,'decoderCalls':0,'uniqueLPSolves':len(audit.records),'solverSeconds':sum(r['solverSeconds'] for r in audit.records)}
            write_once(root/'analysis.json',summary)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','searchFE':0,'decoderCalls':0,'uniqueLPSolvesCompleted':len(audit.records),'error':str(exc)});raise
    finally:audit.log.close()
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'decoderCalls':0,'uniqueLPSolves':len(audit.records),
        'commonFAObstructionSupported':summary['commonFAObstructionSupported'],'wallSeconds':time.monotonic()-start})
    print('FA_REACHABILITY_COMPLETE',[(r['stem'],r['commonFAObstructionSupported']) for r in results],len(audit.records),flush=True)


if __name__=='__main__':main()

"""Fresh actual-search inputs and native legal witness branches, before any full-generator change."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import numpy as np

from teacher_cohort_build import build as capture_build
from pool_phase_build import OBS
from paired_survival_bench import FROZEN,class_hashes
from run_teacher_coupling_probe import capture as old_capture
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from research.reachability.relaxation import FixedFARelaxation,engineering_checks
from research.reachability.prefix_cases import analytic_prefix_checks
from native_branch_analysis import analyze

STEMS=('20_8_5_1','100_2_3_1');SEEDS=(11270003,11270033)


def build_probe(root,capture_cp):
    src,classes=root/'probe-source',root/'probe-classes';src.mkdir();classes.mkdir()
    for name in ('NativeBranchProbe','NativeBranchSupport','ClassResolutionProbe','ReachabilityInstanceExport'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',src)
    for name in ('run_native_branch_value_probe.py','native_branch_analysis.py'):shutil.copy2(Path(__file__).with_name(name),src)
    shutil.copytree(ROOT/'research/reachability',src/'reachability',ignore=shutil.ignore_patterns('__pycache__'))
    execute(['javac','-encoding','UTF-8','--release','8','-cp',capture_cp,'-d',str(classes),*map(str,src.glob('*.java'))],root/'probe-compile.log')
    write_once(root/'probe-class-hashes.json',class_hashes(classes));cp=f'{classes};{capture_cp}'
    (root/'probe-classpath.txt').write_text(cp,encoding='utf-8');return cp


def capture(root,cp,stem,seed,enabled):
    out=root/stem/str(seed)/('ON' if enabled else 'OFF');out.mkdir();inp=root/stem/'inputs'
    cmd=['java','-Xms32m','-Xmx2g','-Dresearch.group.mode=FULL_ROLE','-Dresearch.reward.mode=GROUP','-Dresearch.batch.mode=ROLE_CROWD',
        '-Dresearch.teacherCohort.stepFloor=0',f'-Dresearch.teacherCohort.capture={str(enabled).lower()}',
        '-Dresearch.survival.trace=false','-cp',cp,'research.dynamic.PddrIsolationRun',str(inp/(stem+'.txt')),
        str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(out),'SHARE_JOB_ALIGNED','LINEAR',
        str(out.parent/'ledger.csv'),'5100',str(seed),'100','5100']
    write_once(out/'command.json',cmd);print('NATIVE_SOURCE_CAPTURE',stem,seed,enabled,flush=True);execute(cmd,out/'run.log')
    receipt=rows(out/'run-receipt.jsonl')[0]
    assert receipt['successful']==receipt['attempted']==5100 and receipt['failed']==0
    assert len(receipt['paidSHA256'])==64
    if enabled:
        prior=out.parent/'OFF';assert receipt['paidSHA256']==rows(prior/'run-receipt.jsonl')[0]['paidSHA256']
        for name in ('solutions.jsonl','initial-population.jsonl','local-ledger.csv'):assert (out/name).read_bytes()==(prior/name).read_bytes()
        assert [r['front'] for r in rows(out/'anytime.jsonl')]==[r['front'] for r in rows(prior/'anytime.jsonl')]
        write_once(out/'capture-equivalence.json',{'status':'PASS','all5100PaidSequenceSHAIdentical':True,'genesFrontsInitialsAndLedgerIdentical':True})


def prepare_and_run(root,cp,stem):
    all_cases=[];paid=0;qa=0
    for seed in SEEDS:
        folder=root/stem/str(seed);data=rows(folder/'ON/teacher-cohorts.jsonl')[0]
        centers=[c for c in data['cohorts'] if c['role']=='CENTER'];assert len(centers)==1,'Missing pre-fixed first action2 CENTER; no resampling'
        cohort=centers[0];assert len(cohort['parents'])==8
        initial=rows(folder/'ON/initial-population.jsonl');scales=[sum(p['objectives'][q]/len(initial) for p in initial) for q in range(3)]
        lines=[]
        for p,row in enumerate(cohort['parents']):
            id=f's{seed}-p{p}';noise=int(np.random.default_rng(11380007+seed+p*1009).integers(1,2**62))
            teachers=[row['parent'],row['personal'],row['nativeLeader']];fields=[id,str(noise)]
            for teacher in teachers:fields.extend([','.join(map(str,teacher['objectives'])),*(','.join(map(str,teacher[k])) for k in ('JS','FA','MA','WA'))])
            lines.append('\t'.join(fields));all_cases.append({'id':id,'sourceSeed':seed,'parentIndex':p,'step':cohort['step'],
                'paidSourceFE':cohort['paidFE'],'background':cohort['background'],'teachers':teachers,'constructionSeed':noise})
        path=folder/'cases.tsv';path.write_text('\n'.join(lines)+'\n',encoding='utf-8');inp=root/stem/'inputs'
        cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'org.uma.jmetal.util.research.joint.NativeBranchProbe',str(inp/(stem+'.txt')),
            str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(path),str(folder/'probe'),','.join(map(str,scales))]
        write_once(folder/'probe-command.json',cmd);execute(cmd,folder/'probe.log')
        receipt=rows(folder/'probe/receipt.jsonl')[0];assert receipt['failedFE']==0
        cases=rows(folder/'probe/cases-receipt.jsonl');assert len(cases)==8
        assert receipt['successfulFE']==sum(c['successfulFE'] for c in cases)==24+sum(c['candidates'] for c in cases)
        paid+=receipt['successfulFE'];qa+=receipt['candidateFullQA']
    write_once(root/stem/'manifest.json',{'cases':all_cases})
    inp=root/stem/'inputs'
    execute(['java','-cp',cp,'research.dynamic.ReachabilityInstanceExport',str(inp/(stem+'.txt')),
        str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(root/stem/'physical-coefficients.json')],root/stem/'metadata.log')
    return paid,qa


def fixed_binding_checks():
    stage={'machines':2,'workers':1,'base':[[1,.5]],'energy':[[1,3]],'labor':[[1,.5]]}
    data={'jobs':1,'stages':1,'factories':[[stage]]};result=[]
    for pair,expected in (((0,0),4/3),((1,0),2)):
        record=FixedFARelaxation(data,[0],fixed_stage_zero=[pair]).solve([.75,1.5,1])
        assert abs(record['dual']['lower']-expected)<1e-7
        result.append({'pair':pair,'expected':expected,**record})
    return result


def main():
    root=ROOT/'runs'/datetime.now().strftime('native-branch-value-probe-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('NATIVE_BRANCH_ROOT',root,flush=True);done=[];native_paid=0;native_qa=0
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=[s for s in read(FROZEN/'protocol.json')['instances'] if s['stem'] in STEMS]
            write_once(root/'protocol.json',{'instances':specs,'sourceSeeds':SEEDS,'sourceCaptureFE':40800,'primary':'LP_TIME',
                'scope':'New candidate-context experiment; old final-prefix information gates remain failed. Original mainline is not using this diagnostic generator. Actual QGS inputs feed unchanged native JointCandidates/BlockContext in isolation.',
                'sources':'First actual generation1 action2 CENTER batch, stepFloor0 specified before outcomes,8 equally spaced free parents, two fresh source seeds per instance. All16 cases retained; missing windows are missing, no replacement seed or quality resampling.',
                'engineering':'OFF/ON5100 full paid SHA must be real64hex and identical; full FE fronts/genes/initials/ledger too. Original models, FULL_ROLE, oldest personal semantics, serial/stale guidance, Q/family/sharing unchanged. Only observation threshold configurable; its default remains24 for previous workflows.',
                'candidates':'Native block length4, original objective-blind at-most6 action sources, original legal witness coverage. Each action is materialized into a designated complete legal witness. This is one-step designated-completion ranking, not a bound over every later guided construction or variable FA continuation.',
                'inputsAndLabels':'All3 source replays and every available complete witness evaluated through RunContext, including duplicates. Each completed witness full-decoded with exact timeline QA. Scores read input-only prefix/genome/paid-parent features first and are saved before outcome files are loaded. Parents/teachers added to old background so copying earns no new HV.',
                'scores':'GREEDY partial normalized sum; native JointFeatures TAIL_SUM and TAIL_RAY on the designated witness; CHEAP_RAY maximum separated physical bound. LP_TIME fixes witness FA and future stage0 bindings while relaxing later resources/order/fatigue. LP_FATIGUE=max(LP_TIME,min(conditionalFatigueLP,1)), a valid global parent-relative ray bound despite the finite fatigue horizon. Sum/ray controls prevent aggregation confounding.',
                'labels':'Single-candidate HV addition over the actual pre-batch paid archive, true max(objectives/parentObjectives), same-pool regret and rank correlation. RANDOM is uniform expected gain over that same pool. Ties use1e-12 relative tolerance and mean outcome, never favorable selection.',
                'qualityGate':'Both instances >=8/16 cases have best addedHV>1e-10. Primary LP_TIME mean selected addedHV >=10% above EACH pre-fixed cheap rule, >=20% over random. Fatigue independent question additionally >=5% above LP_TIME and its own cheap/random gates. Failure stops these scores without changing aspirational targets, block length, data windows or weights.',
                'costGate':'On each instance median(LP score-all plus selected evaluation)/(evaluate every same-pool witness)<=1. Common construction cancels; IO omitted favors LP. If this necessary cost gate fails, no complete-generator experiment. This is actual implementation cost preflight, not a closed-loop same-time or same-FE result.',
                'accounting':'8source replays x5100=40800FE plus actual native input3+candidate-count per case <=288FE. QA and explicit prefix appends, feature preparation, all score times and LP solves separately counted. Offline predictions do not become extra method runs or free training evaluations.',
                'preserved':'No default algorithm, new RL, Q parameters, native candidate sources or shared-pool changes; no public upload. A pass only permits a fresh controlled generator protocol.'})
            checks=engineering_checks()+analytic_prefix_checks()+fixed_binding_checks();write_once(root/'engineering-checks.json',{'status':'PASS','LPCalls':len(checks),'checks':checks})
            cap=root/'capture-build';cap.mkdir();capture_cp=capture_build(cap);cp=build_probe(root,capture_cp)
            original_cp=(OBS/'classpath.txt').read_text(encoding='utf-8-sig').strip()
            for stem in STEMS:
                shutil.copytree(FROZEN/'inputs'/stem,root/stem/'inputs')
                for seed in SEEDS:
                    folder=root/stem/str(seed);folder.mkdir();(folder/'ledger.csv').write_text('visit,group,round,factory,paid,restarts\n',encoding='utf-8')
                    capture(root,original_cp,stem,seed,False);capture(root,capture_cp,stem,seed,True);done.append([stem,seed])
                paid,qa=prepare_and_run(root,cp,stem);native_paid+=paid;native_qa+=qa
            result=analyze(root,specs,SEEDS)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','sourcePairsCompleted':done,'nativePaidFECompleted':native_paid,'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulSourceFE':40800,'successfulNativeFE':native_paid,'failedEvaluationFE':0,
        'nativeFullDecoderQA':native_qa,'sourceReturnFullDecoderQA':sum(read(p)['offlineValidationDecodes'] for p in root.glob('*/*/*/summary.json')),
        'worthGeneratorExperiment':result['worthGeneratorExperiment'],'worthFatigueExperiment':result['worthFatigueExperiment']})
    print('NATIVE_BRANCH_COMPLETE',result,flush=True)


if __name__=='__main__':main()

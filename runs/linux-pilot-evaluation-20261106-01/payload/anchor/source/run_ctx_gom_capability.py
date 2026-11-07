"""Prospective light acceptance and complete new-seed full-algorithm pilot; preserve stopped versions."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil
import sys

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from run_qpa_complete_engineering import protected
from ctx_gom_build import BASE, build
from ctx_gom_capability_support import ENGINE, ARMS, counts, engineering, run_case
from ctx_gom_capability_analysis import analyze
from pa_capability_support import initial_key
from research.semantic_repair.evidence import digest

CONTRACT = ROOT/'research/gomea_reference_audit/CTX_GOM_CAPABILITY_V1.json'


def protocol():
    return dict(version='CTX_GOM_COMPLETE_CAPABILITY-v1',registered='2026-11-06',engineeringAccepted=str(ENGINE),
        instances=read(BASE/'protocol.json')['instances'],seeds=[14910003,14910037],arms=ARMS,
        primary='SHARE_CTX_GOM fixed across instances/budgets; never promote a better ablation/control posthoc',
        architecture='Original QGS/four physical roles/fixed families/conditional sharing/outer retention; context-aware fullGOM replaces entire local phase, with live compatible donors and ordinary strict-boundary PA acceptance',
        unchanged='No new selector, Q table, FI, quota/phase-ratio/threshold scan, operator or seed replacement; protected default files unchanged',
        light='Only disable detailed events, paid/view full QA and source-provenance bookkeeping; keep model/genome/RNG/acceptance/archive/legality/clock operations',
        engineeringSeed=14810003,fixedLightEngineeringFE=392936,maximumLightEngineeringAttempts=412936,
        engineering='Eight full two-pass light traces equal old heavy paidSHA/initial100/front; all six complete control entries old-vs-new5102FE in bothinstances; four real0.2s clock tests capped5000attempts each',
        fixedFE=500000,plannedFixedScienceFE=20000000,timeSafetyFE=5000000,
        phases=['Complete all40 FE500K runs','Complete all40 TIME runs iff competitivePass for BOTH instances'],
        timeRule='Previous registered4s/5s, separate sequential fresh JVMs, common observer/archives, constructors and all algorithm costs insideclock; checkpoint QA outside',
        initialization='Exactly same100 canonical fourvectors/objectives in all ten arms paired per newseed; no reused objective feedback',
        indicators='HV1.5 plus1.25/2 sensitivity; common per-instance per-phase NDunion of all10arms/all2seeds as empirical IGD+reference; exactdeduplicated weak bidirectionalC includingequal, report coveredcounts and front sizes',
        improvementControls=['FULL_SHARED_DEEP','LI_RECON_DEEP','NSGA2_PLAIN'],
        improvementRule='For eachinstance vs each listed control: medianHV1.5>=1%, HV1.25/2>=0; medianIGD+symmetricworsening<=0 and median(CAB-CBA)>=0. Everyseed HV>=-1%, IGD+worsening<=5%, Cdelta>=-.02',
        noninferiorityControls=['NSGA2_DEEP','NSGA_CTX_GOM','PA_JOINT','PA_EQUAL'],
        noninferiorityRule='For eachinstance vs each strongcontrol: medianHV>=-1%atall3references, medianIGD+worsening<=5%, medianCdelta>=-.02. Everyseed HV1.5>=-3%, IGD+worsening<=10%, Cdelta>=-.05. This is an exploration screen, not a superiority claim',
        mechanismControls=['SYNC_CTX_GOM','UNIFORM_CTX_GOM'],
        mechanismRule='Separately eachinstance vs each ablation: medianHV1.5>=.5%, HV1.25/2>=0, medianIGD+worsening<=0, medianCdelta>=0, everyseed HV>=-1%, IGD+worsening<=5%, Cdelta>=-.02. No 2of3vote',
        competitivePass='All registered improvement and strongcontrol noninferiority conditions on bothinstances; independent mechanisms recorded separately, cannot substitute for competition',
        progression='Only if FEcompetitive pass start allTIME. Bothbudgetscompetitive plus bothmechanism checks permits a new heldout-confirmation protocol, never claims final goal achieved',
        order='Rotate fixed ten-arm list by(instanceIndex+seedIndex), complete all40 before result-dependent decision; stagecurves descriptive only',
        failure='Preserve failures/costs/front and stop engineering or phase on unexpected fault. Negative/metric-conflicting fixed primary stops this version, no parameter/seed/horizon rescue',
        scope='Same two reused eligible development instances, two fresh seeds. No multi-instance expansion, manuscript novelty assertion or default integration',
        oldStopsUnchanged=True,externalTransfers=False,defaultMainlineChanged=False,goalAchieved=False)


def phase(root,cp,plan,kind):
    for i,spec in enumerate(plan['instances']):
        stem = spec['stem']
        for k,seed in enumerate(plan['seeds']):
            shift = (i+k)%len(ARMS); order = ARMS[shift:]+ARMS[:shift]; initial = None
            for arm in order:
                limit = plan['fixedFE'] if kind == 'FE500K' else plan['timeSafetyFE']
                seconds = float('inf') if kind == 'FE500K' else spec['time_seconds']
                out,_ = run_case(root,cp,stem,arm,f'{seed}/{kind}-{arm}',limit,seed,seconds)
                current = initial_key(out); assert len(current) == 100
                if initial is None: initial = current
                assert current == initial
                if kind == 'TIME': assert current == initial_key(root/stem/str(seed)/('FE500K-'+arm))
    result = analyze(root,plan,kind); print('CTX_CAPABILITY_DECISION',kind,result['competitivePass'],result['independentRoleAndSharingPass'],flush=True)
    return result


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        resume = len(sys.argv) > 1
        root = Path(sys.argv[1]).resolve() if resume else ROOT/'runs'/datetime.now().strftime('ctx-gom-capability-%Y%m%d-%H%M%S-%f')
        print('CTX_CAPABILITY_ROOT',root,flush=True)
        if resume:
            plan = read(root/'protocol.json'); before = read(root/'protected-before.json')
            cp = (root/'classpath.txt').read_text('utf-8-sig').strip()
            for name,sha in read(root/'source-hashes.json').items(): assert digest(root/name) == sha
            write_once(root/'resume-controller.json',dict(reason='Revalidate complete records; never replace partial/evaluation failures',controllerSHA256=digest(Path(__file__))))
        else:
            plan = protocol(); assert read(ENGINE/'status.json')['engineeringPass']; root.mkdir(); before = protected()
            if CONTRACT.exists(): assert read(CONTRACT) == plan
            else: write_once(CONTRACT,plan)
            write_once(root/'protocol.json',plan); write_once(root/'protected-before.json',before)
            for spec in plan['instances']:
                stem = spec['stem']; shutil.copytree(ENGINE/stem/'inputs',root/stem/'inputs')
                write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in (root/stem/'inputs').iterdir() if p.is_file()})
            _,cp = build(root,extra_python=('ctx_gom_capability_support.py','ctx_gom_capability_analysis.py','run_ctx_gom_capability.py','qpa_capability_analysis.py'))
        try:
            if (root/'light-engineering.json').exists(): assert read(root/'light-engineering.json')['passed']
            else: engineering(root,cp,plan)
            engineering_fees = counts(root)
            results = [read(root/'fe500k-analysis.json') if (root/'fe500k-analysis.json').exists() else phase(root,cp,plan,'FE500K')]
            if not resume: assert counts(root)['successfulFE'] == engineering_fees['successfulFE']+plan['plannedFixedScienceFE']
            if results[0]['competitivePass']:
                results.append(phase(root,cp,plan,'TIME'))
            competitive = len(results)==2 and all(r['competitivePass'] for r in results)
            mechanism = competitive and all(r['independentRoleAndSharingPass'] for r in results)
            decision = 'READY_FOR_SEPARATE_HELDOUT_PROTOCOL' if mechanism else 'COMPETITIVE_BUT_INDEPENDENT_MECHANISMS_UNPROVEN' if competitive else 'STOP_FIXED_CTX_GOM_CAPABILITY'
            assert protected() == before
            for name,sha in read(root/'source-hashes.json').items(): assert digest(root/name) == sha
            write_once(root/'analysis.json',dict(phases=results,decision=decision,**counts(root),sameTimeExecuted=len(results)==2,
                defaultMainlineChanged=False,oldStopsUnchanged=True,heldoutExecuted=False,goalAchieved=False))
        except BaseException as error:
            target = 'resumed-status.json' if resume else 'status.json'
            write_once(root/target,dict(status='INCOMPLETE_RETAINED',error=repr(error),**counts(root),goalAchieved=False)); raise
        write_once(root/('resumed-status.json' if resume else 'status.json'),dict(status='COMPLETE',decision=decision,**counts(root),goalAchieved=False))
        print('CTX_CAPABILITY_COMPLETE',decision,counts(root),flush=True)


if __name__ == '__main__': main()

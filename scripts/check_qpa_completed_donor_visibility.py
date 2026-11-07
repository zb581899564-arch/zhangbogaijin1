"""Registered zero-FE precondition for isolating the ordinary donor-feedback lifecycle."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from datetime import datetime
from pathlib import Path
import shutil
import time

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from research.semantic_repair.evidence import digest
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from run_qpa_complete_engineering import protected
from qpa_donor_visibility import analyze

SOURCE=ROOT/'runs/qpa-complete-engineering-20261106-024925-292174'


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        start=time.perf_counter();root=ROOT/'runs'/datetime.now().strftime('qpa-completed-donor-visibility-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('QPA_DONOR_VISIBILITY_ROOT',root,flush=True);before=protected()
        write_once(root/'protocol.json',dict(version='QPA_COMPLETED_DONOR_VISIBILITY-v1',registeredBeforeCalculation=True,source=str(SOURCE),
            hypothesis='QPA_DIRECT freezes all100donors until generation end whereas PA uses live accepted states. Determine how many actual paid proposals would physically differ if only already-completed donor programs were visible. No score or causal performance inference.',
            inputs='Existing complete engineering firsttwogenerations ofboth20_8_5_1/100_2_3_1, seed14670003; no timewindow/source/seed sampling',
            intervention='On each actual SYNCtrajectory, substitute completed offspring[donorSlot] only when donorSlot<receiverSlot; same actual parent,mask,phase,reference andlegalmove. Bothphases measured separately on their actual incumbents, no propagation of unknown acceptance.',
            selfAndFuture='Ownslot and not-yet-completed donors stay frozen. Input models,order,RNG,references,operators,objective acceptance andbudget unchanged.',
            necessaryCoverage='Bothinstances require counterfactualPhysicalChange >=20%ofallpaidmixingsteps and crossRolePhysicalChange>=5%; otherwise stop this specific donor-feedback explanation, no cutoff scan',
            accounting='Count unscored complete integer proposals explicitly. No DynamicDecoder/objective/oracleHVquery/searchfeedback. Known old/source objectives not reused as counterfactual objectives.',
            progression='Coverage only can justify separatelyregistered SYNC/LIVE_SAME_ROLE/LIVE_ALL lifecycle ablation. It is not performance or four-role contribution. Prior independenthalfpool/role/source/learning stops stay stopped.',
            protectedBefore=before,newSearchFE=0,newDecoderCalls=0,defaultMainlineChanged=False,goalAchieved=False))
        for name in ('check_qpa_completed_donor_visibility.py','qpa_donor_visibility.py'):shutil.copy2(Path(__file__).with_name(name),root/name)
        cp=(SOURCE/'classpath.txt').read_text('utf-8-sig').strip();assert class_hashes(SOURCE/'classes')==read(SOURCE/'class-hashes.json')
        results=[]
        for stem in ('20_8_5_1','100_2_3_1'):
            folder=SOURCE/stem/'main';catalog,=rows(folder/'catalog.jsonl');receipt,=rows(folder/'receipt.jsonl')
            capture,=rows(folder/'loaded-identity.jsonl');verify_capture(capture,cp)
            write_once(root/(stem+'-source-identities.json'),{n:digest(folder/n) for n in ('events.jsonl','receipt.jsonl','catalog.jsonl','loaded-identity.jsonl')})
            result=analyze(folder,catalog,receipt);results.append(dict(instance=stem,seed=catalog['seed'],**result))
            print('DONOR_VISIBILITY',stem,result['physicalChangedFraction'],result['crossRoleChangedFraction'],flush=True)
        assert protected()==before
        passed=all(r['coveragePass'] for r in results)
        write_once(root/'analysis.json',dict(instances=results,necessaryCoveragePass=passed,
            decision='VISIBILITY_ONLY_SEPARATE_LIFECYCLE_CAUSAL_PROTOCOL_REQUIRED' if passed else 'STOP_FIXED_COMPLETED_DONOR_FEEDBACK_EXPLANATION',
            wallSeconds=time.perf_counter()-start,newSearchFE=0,newDecoderCalls=0,objectiveCalls=0,defaultMainlineChanged=False,goalAchieved=False))
        print('QPA_DONOR_VISIBILITY_COMPLETE',passed,flush=True)


if __name__=='__main__':main()

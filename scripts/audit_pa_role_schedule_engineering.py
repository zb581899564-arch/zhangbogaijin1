"""Final identity/accounting audit of completed role-trace proofs, including retained-run reuse."""
from pathlib import Path
import shutil
import sys

from run_long_budget_bridge import ROOT,read,rows,write_once
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture,resolve_class
from pa_role_engineering_support import receipts
from run_pa_role_schedule_engineering import first_model


def actual(folder):
    return Path(read(folder/'reuse.json')['source']) if (folder/'reuse.json').exists() else folder


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract']
    assert read(root/'status.json')['engineeringPass'] and read(root/'acceptance.json')['passed']
    assert protected()==protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/PA_ROLE_SCHEDULE_ENGINEERING_V1.json')==protocol['contractSHA256']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    hashes=read(root/'class-hashes.json');assert class_hashes(root/'classes')==hashes['wrapper'] and class_hashes(root/'kernel-classes')==hashes['planner']
    cp=(root/'classpath.txt').read_text('utf-8-sig').strip()
    for name,value in read(root/'inherited-identities.json').items():assert resolve_class(cp,name)==value
    checked=[]
    for spec in plan['cases']:
        stem=spec['stem'];native_model=first_model(actual(root/stem/'NATIVE'))
        for name,sha in read(root/stem/'input-hashes.json').items():assert digest(root/stem/'inputs'/name)==sha
        for mode in plan['modes']:
            folder=actual(root/stem/mode);record,=rows(folder/'receipt.jsonl');proof=read(folder/'role-independent-replay.json')
            assert record['attemptedFE']==record['successfulFE']==record['decoder']['dynamic.evaluations']==record['paidFullTimelineQA']==spec['masterFE']
            assert record['failedFE']==0 and proof['passed'] and proof['allReceiverOrdersAndAcceptsVerified']
            assert record['completedGenerations']==proof['completedGenerations']==2 and record['completedPrograms']==200
            assert first_model(folder)==native_model
            command=read(folder/'command.json');original_cp=command[command.index('-cp')+1]
            capture,=rows(folder/'loaded-identity.jsonl');capture.update(read(folder/'role-identity.json'));verify_capture(capture,original_cp)
            for name,value in capture.items():
                if isinstance(value,dict) and 'sha256' in value:assert resolve_class(cp,name)['sha256']==value['sha256']
            if mode=='NATIVE':
                old,=rows(Path(plan['sourceEngineering'])/stem/'main/audit/receipt.jsonl')
                assert old['paidSHA256']==record['paidSHA256'] and old['lastValidFront']==record['lastValidFront']
            checked.append(dict(instance=stem,mode=mode,allPaidTimelineAndRoleVisitReplayPassed=True,firstPhysicalModelNativeEqual=True))
        master=read(root/stem/'FULL/role-independent-replay.json')
        for limit in spec['cutoffs']:
            record,=rows(root/stem/('cut'+str(limit))/'receipt.jsonl')
            assert record['successfulFE']==limit and record['paidSHA256']==master['prefixSHA256'][str(limit)]
            assert read(root/stem/('cut'+str(limit))/'role-independent-replay.json')['passed']
    totals=receipts(root)
    assert totals['runs']==24 and totals['successfulFE']==totals['attemptedFE']==plan['plannedFixedFE']<=plan['maximumActualAttemptedFE']
    assert totals['newAttemptedFE']==303746 and totals['reusedAttemptedFE']==7900 and totals['failedFE']==0
    write_once(root/'independent-final-audit.json',dict(passed=True,checks=checked,**totals,fullRoleAndProgramEvidenceAccepted=True,
        retained7900FEReusedWithoutSearch=True,postprocessingAndCommandIndexFailuresRetained=True,newSearchFE=0,newDecoderCalls=0,performanceProved=False,goalAchieved=False))
    directory=root/'independent-audit-source';directory.mkdir();shutil.copy2(Path(__file__),directory)
    print('PA_ROLE_ENGINEERING_FINAL_AUDIT_PASS',totals,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

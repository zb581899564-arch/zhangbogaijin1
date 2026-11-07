"""No-search final acceptance: effective classes, exact native behavior and every cutoff."""
from pathlib import Path
import shutil
import sys

from run_long_budget_bridge import ROOT,read,rows,write_once
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import verify_capture,resolve_class
from paired_survival_bench import class_hashes
from run_pa_role_schedule_engineering import first_model
from pa_regional_engineering_support import totals


def verify_run(root,spec,label,mode,limit):
    folder=root/spec['instance']/label;cmd=read(folder/'command.json');at=cmd.index('research.dynamic.PaRegionalEngineeringRun')
    assert cmd[at+6:]==['13630003',str(limit)] and Path(cmd[at+5])==folder
    assert '-Dresearch.paRegional.mode='+mode in cmd
    receipt,=rows(folder/'receipt.jsonl');proof=read(folder/'regional-independent-replay.json')
    assert receipt['status']=='COMPLETE' and proof['passed'] and proof['mode']==mode and proof['paidFE']==limit
    assert receipt['successfulFE']==receipt['attemptedFE']==receipt['decoder']['dynamic.evaluations']==receipt['paidFullTimelineQA']==limit
    assert receipt['failedFE']==0 and proof['paidSHA256']==receipt['paidSHA256']
    capture,=rows(folder/'loaded-identity.jsonl');cp=cmd[cmd.index('-cp')+1];verify_capture(capture,cp)
    helper=read(folder/'regional-policy.json');verify_capture(helper['identity'],cp);policy=helper['policy']
    if mode=='OFF':assert policy['observedPaid']==0 and not policy['targetsReady'] and (folder/'regional-events.jsonl').stat().st_size==0
    else:
        program=2*receipt['jobs']-1;paid=max(0,limit-100);complete,remainder=divmod(paid,100*program)
        center=complete*55*program+min(max(0,remainder-15*program),55*program)
        assert policy['observedPaid']==limit and policy['centerComparisons']==center and policy['boundaryComparisons']==paid-center
        assert policy['targetsReady']==(limit>=100)
        if limit==spec['firstCenterPaidFE']:assert policy['centerComparisons']==1
    return receipt,proof


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract']
    assert read(root/'status.json')['status']=='COMPLETE' and protected()==protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/PA_CENTER_REGIONAL_ENGINEERING_V1.json')==protocol['contractSHA256']
    assert digest(Path(plan['opportunityRoot'])/'independent-final-audit.json')==plan['opportunityAuditSHA256']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    hashes=read(root/'class-hashes.json')
    assert class_hashes(root/'classes')==hashes['policy'] and class_hashes(root/'math-classes')==hashes['math']
    cp=(root/'classpath.txt').read_text('utf-8-sig').strip()
    for name,value in read(root/'inherited-identities.json').items():assert resolve_class(cp,name)==value
    original=Path(plan['populationSource']).read_text('utf-8');adapted=(root/'source/PaPopulation.java').read_text('utf-8')
    start='    private List<int[]> learn()';end='    public List<PaIndividual> population()'
    assert original[original.index(start):original.index(end)]==adapted[adapted.index(start):adapted.index(end)]
    # The independent scalar/assignment calculations ran before search; verify their retained evidence.
    validate_copy=root/'math-acceptance.json';before=digest(validate_copy)
    assert read(validate_copy)['passed'] and len(read(root/'math-output.json')['fixtures'])==5
    checks=[]
    for spec in plan['cases']:
        stem=spec['instance'];native=first_model(root/stem/'OFF')
        for name,sha in read(root/stem/'input-hashes.json').items():assert digest(root/stem/'inputs'/name)==sha
        for mode in plan['modes']:
            receipt,proof=verify_run(root,spec,mode,mode,spec['masterFE'])
            assert receipt['completedGenerations']==proof['completedGenerations']==2 and receipt['completedPrograms']==200
            assert first_model(root/stem/mode)==native
            if mode=='OFF':
                old,=rows(Path(spec['source'])/'receipt.jsonl');assert receipt['paidSHA256']==old['paidSHA256'] and receipt['lastValidFront']==old['lastValidFront']
            checks.append(dict(instance=stem,mode=mode,firstPhysicalModelNativeEqual=True,fullPaidTimelineAndPolicyReplayPassed=True))
        for mode in ('REGIONAL','NO_SPECIALIST'):
            master=read(root/stem/mode/'regional-independent-replay.json')
            for limit in spec['cutoffs']:
                receipt,_=verify_run(root,spec,mode+'-cut'+str(limit),mode,limit)
                assert receipt['paidSHA256']==master['prefixSHA256'][str(limit)]
    actual=totals(root);assert actual['runs']==30 and actual['attemptedFE']==actual['successfulFE']==plan['plannedActualAttemptedFE']==199760
    assert actual['attemptedFE']<=plan['maximumActualAttemptedFE'] and actual['failedFE']==0 and before==digest(validate_copy)
    write_once(root/'independent-final-audit.json',dict(passed=True,checks=checks,**actual,
        nativeWholePaidTraceAndFrontEqual=True,initialTargetsAndEveryFirstCenterCutVerified=True,
        originalLearnAndNativeAcceptFunctionsUnchanged=True,allClassesInputsSourcesAndChargesVerified=True,
        newSearchFE=0,newDecoderCalls=0,performanceProved=False,defaultMainlineChanged=False,goalAchieved=False))
    folder=root/'independent-audit-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('PA_CENTER_REGIONAL_ENGINEERING_FINAL_AUDIT_PASS',actual,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

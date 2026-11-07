"""Final no-search audit of the nine-arm regional pilot and explicit ordinary MOEA/D."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
import shutil
import sys

from run_long_budget_bridge import ROOT,read,rows,write_once
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class
from ctx_gom_capability_support import checked,counts
from pa_capability_support import initial_key
from pa_role_pilot_support import supplied_initials
from qpa_capability_analysis import endpoint
from pa_role_pilot_metric_audit import verify as metric_audit
from pa_regional_pilot_support import check_moead,check_policy
from audit_qpa_completed_donor_pilot import flags
import numpy as np


def command_check(root,folder,plan,spec,arm,seed,limit,old=False,reference=False,supplied=None):
    real,mode=plan['armDefinitions'][arm];template='NSGA2_DEEP' if real=='MOEAD_4V' else real
    original=read(Path(plan['controlSource'])/spec['stem']/'14910003'/('FE500K-'+template)/'command.json');cmd=read(folder/'command.json')
    vm,options=flags(cmd);oldvm,oldoptions=flags(original);assert vm==oldvm
    expected={'research.paRegional.mode':mode,'research.paRegional.scale':','.join(map(str,spec['normalization']['scale'])),
        'research.pa.auditPaid':'true','research.pa.traceIdentity':'false','research.ctxFork.localInput':'POST'}
    if supplied:expected['research.pa.sourceTSV']=str(supplied)
    if real=='MOEAD_4V':expected.update({'research.moead.reference':str(reference).lower(),'research.ctxGom.enabled':'false'})
    assert options==dict(oldoptions,**expected)
    entry='research.dynamic.PlainMoeadRun' if real=='MOEAD_4V' else 'research.dynamic.GomCapabilityRun' if old else 'research.dynamic.PaRegionalCapabilityRun'
    at=cmd.index(entry);assert cmd[at+4:]==[str(folder),real,str(limit),str(seed),'Infinity']
    for offset,name in enumerate((spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),1):assert Path(cmd[at+offset])==root/spec['stem']/'inputs'/name
    receipt=checked(folder,cmd[cmd.index('-cp')+1],limit,float('inf'))
    assert receipt['seed']==seed and receipt['arm']==real and receipt['decoder']['dynamic.evaluations']==limit and receipt['paidSHA256']
    if real=='MOEAD_4V':check_moead(folder,receipt,limit,reference)
    elif not old:check_policy(folder,mode,np.asarray(spec['normalization']['scale']),limit,real)
    return receipt


def bridges(root,plan):
    engine=Path(plan['engineeringRoot'])
    for spec in plan['instances']:
        stem=spec['stem'];supplied=engine/stem/'inputs/sources.tsv'
        for arm,mode in (('PA_JOINT','OFF'),('REGIONAL','REGIONAL'),('NO_SPECIALIST','NO_SPECIALIST')):
            folder=root/stem/('BRIDGE-'+arm);r=command_check(root,folder,plan,spec,arm,13630003,spec['engineeringFE'],supplied=supplied)
            old,=rows(engine/stem/mode/'receipt.jsonl')
            assert r['paidSHA256']==old['paidSHA256'] and initial_key(folder)==supplied_initials(supplied)
            assert sorted(map(tuple,endpoint(folder,'FE',spec['engineeringFE'])['front']))==sorted(tuple(p['objectives']) for p in old['lastValidFront'])
        initial=None
        for arm in plan['bridgeControls']:
            a,b=[root/stem/('BRIDGE-'+tag+'-'+arm) for tag in ('OLD','NEW')]
            ra=command_check(root,a,plan,spec,arm,13630003,5102,old=True);rb=command_check(root,b,plan,spec,arm,13630003,5102)
            assert ra['paidSHA256']==rb['paidSHA256'] and initial_key(a)==initial_key(b)
            assert endpoint(a,'FE',5102)['front']==endpoint(b,'FE',5102)['front']
            if initial is None:initial=initial_key(a)
            assert initial==initial_key(a)
        for limit in [5102]+plan['moeadCutoffs']:
            suffix='' if limit==5102 else '-cut'+str(limit);records=[]
            for reference in (True,False):
                folder=root/stem/('BRIDGE-MOEAD-'+('REFERENCE' if reference else 'CURRENT')+suffix)
                records.append(command_check(root,folder,plan,spec,'MOEAD_4V',13630003,limit,reference=reference))
                if limit==5102:assert initial_key(folder)==initial
            assert records[0]['paidSHA256']==records[1]['paidSHA256']
            a=root/stem/('BRIDGE-MOEAD-REFERENCE'+suffix);b=root/stem/('BRIDGE-MOEAD-CURRENT'+suffix)
            assert endpoint(a,'FE',limit)['front']==endpoint(b,'FE',limit)['front']


def source_check(root,plan):
    adaptation=read(root/'moead-source-adaptation.json')
    for key in ('deepSource','originalSource'):assert digest(Path(adaptation[key]))==adaptation[key+'SHA256']
    texts=[Path(plan[name]).read_text('utf-8') for name in ('moeadDeepSource','moeadOriginalSource')]
    texts.extend((root/'source'/name).read_text('utf-8') for name in ('OrdinaryMoeadAlgorithm.java','MoeadReferenceAlgorithm.java'))
    start,end='    private void runMoead()','    private List<Integer> matingPool('
    assert len({text[text.index(start):text.index(end)] for text in texts})==1
    assert 'if (!"MOEAD_4V".equals(config.mode))' in texts[2] and 'if (!"MOEAD_4V".equals(config.mode))' in texts[3]
    assert 'deep.prepareInitial(initial, i)' in texts[2] and 'initial.prepare(point, i)' in texts[3]
    assert not adaptation['existingClassicAlgorithmOverridden'] and not adaptation['localSearchInvoked']


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert read(root/'status.json')['status']=='COMPLETE' and read(root/'bridge-acceptance.json')['passed']
    assert digest(ROOT/'research/gomea_reference_audit/PA_CENTER_REGIONAL_PILOT_V1.json')==protocol['contractSHA256']
    amendment=read(ROOT/'research/gomea_reference_audit/PA_CENTER_REGIONAL_PILOT_ENGINEERING_AMENDMENT_V1.json')
    assert protocol['engineeringAmendment']==amendment and read(Path(amendment['previousFailure'])/'status.json')['attemptedFE']==0
    assert digest(Path(plan['engineeringRoot'])/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    assert protected()==protocol['protectedBefore'];hashes=read(root/'class-hashes.json')
    assert class_hashes(root/'classes')==hashes['wrapper'] and class_hashes(root/'kernel-classes')==hashes['kernel']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    cp=(root/'classpath.txt').read_text('utf-8-sig').strip()
    for name,value in read(root/'inherited-identities.json').items():assert resolve_class(cp,name)==value
    source_check(root,plan);bridges(root,plan);instances=[]
    for spec,item in zip(plan['instances'],result['instances']):
        assert item['instance']==spec['stem']
        for name,sha in read(root/spec['stem']/'input-hashes.json').items():assert digest(root/spec['stem']/'inputs'/name)==sha
        for seed in plan['seeds']:
            initial=None
            for arm in plan['arms']:
                folder=root/spec['stem']/str(seed)/('FE-'+arm);r=command_check(root,folder,plan,spec,arm,seed,spec['fixedFE'])
                row,=[v for v in item['observations'] if v['seed']==seed and v['arm']==arm]
                assert row['successfulFE']==r['successful'] and row['searchSeconds']==r['searchSeconds'] and row['stageFE']==r['search']
                current=initial_key(folder)
                if initial is None:initial=current
                assert len(current)==100 and current==initial
        instances.append(metric_audit(root,item,spec,plan))
    actual=counts(root);assert actual['runs']==82 and actual['attemptedFE']==actual['successfulFE']==plan['plannedTotalAttemptedFE']==3866664
    assert actual['failedFE']==actual['timeInterruptedAttempts']==0 and actual['attemptedFE']<=plan['maximumTotalAttemptedFE']
    for key,value in actual.items():assert result[key]==value
    assert result['pass_']==all(v['pass_'] for v in instances)
    expected='ORDINARY_REGIONAL_SIGNAL_ONLY_SEPARATE_INTEGRATION_REQUIRED' if result['pass_'] else 'STOP_FIXED_REGIONAL_CENTER_PILOT'
    assert result['decision']==expected and not result['sameTimeTested'] and not result['goalAchieved']
    write_once(root/'independent-final-audit.json',dict(passed=True,instances=instances,**actual,allIndicatorsCountsCriteriaAndInitialsVerified=True,
        acceptedKernelBytesAndAllBridgesVerified=True,explicitMoeadExecutedAndPairedSourcesVerified=True,zeroFECompileFailureRetained=True,
        newSearchFE=0,newDecoderCalls=0,defaultMainlineChanged=False,goalAchieved=False))
    folder=root/'independent-audit-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('PA_CENTER_REGIONAL_PILOT_FINAL_AUDIT_PASS',actual,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

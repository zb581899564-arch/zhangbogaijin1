"""Final no-search audit of role mappings, bridges, identities, accounting and metrics."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
import shutil
import sys

from run_long_budget_bridge import ROOT,read,rows,write_once
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture,resolve_class
from research.semantic_repair.evidence import digest
from ctx_gom_capability_support import counts,checked
from qpa_capability_analysis import endpoint
from pa_capability_support import initial_key
from pa_role_pilot_support import actual,supplied_initials,verify_roles
from audit_qpa_completed_donor_pilot import flags
from pa_role_pilot_metric_audit import verify as metric_audit


def command_check(root,folder,plan,spec,arm,seed,limit,old=False,supplied=None):
    real,mode=plan['armDefinitions'][arm];qpa=real=='QPA_DIRECT'
    source=Path(plan['qpaSource'] if qpa else plan['controlSource'])/spec['stem']/('14730003' if qpa else '14910003')/('FE500K-'+real)
    cmd,original=read(folder/'command.json'),read(source/'command.json')
    vm,settings=flags(cmd);oldvm,oldsettings=flags(original);assert vm==oldvm
    expected={'research.paRole.mode':mode,'research.paRole.seed':str(plan['privateSeed']),'research.paRole.fullTrace':'false',
        'research.pa.auditPaid':'true','research.pa.traceIdentity':'false','research.ctxFork.localInput':'POST'}
    if supplied:expected['research.pa.sourceTSV']=str(supplied)
    assert settings==dict(oldsettings,**expected)
    entry=('research.dynamic.QpaCapabilityRun' if qpa else 'research.dynamic.GomCapabilityRun') if old else 'research.dynamic.PaRoleCapabilityRun'
    at=cmd.index(entry);assert cmd[at+5:]==[real,str(limit),str(seed),'Infinity'] and Path(cmd[at+4])==folder
    for offset,name in enumerate((spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),1):assert Path(cmd[at+offset])==root/spec['stem']/'inputs'/name
    cp=cmd[cmd.index('-cp')+1];receipt=checked(folder,cp,limit,float('inf'))
    assert receipt['seed']==seed and receipt['arm']==real and receipt['decoder']['dynamic.evaluations']==limit
    if not old:
        verify_capture(read(folder/'role-identity.json'),cp)
        assert verify_roles(folder,mode,plan['privateSeed'])==read(folder/'role-mapping-audit.json')
    return receipt


def bridges(root,plan):
    engine=Path(plan['engineeringRoot'])
    for spec in plan['instances']:
        stem=spec['stem'];supplied=engine/stem/'inputs/sources.tsv'
        for mode in plan['modes']:
            folder=root/stem/('BRIDGE-'+mode);r=command_check(root,folder,plan,spec,mode,13630003,spec['engineeringFE'],supplied=supplied)
            previous,=rows(actual(engine/stem/mode)/'receipt.jsonl')
            assert r['paidSHA256']==previous['paidSHA256'] and initial_key(folder)==supplied_initials(supplied)
            assert sorted(map(tuple,endpoint(folder,'FE',spec['engineeringFE'])['front']))==sorted(tuple(p['objectives']) for p in previous['lastValidFront'])
        for arm in plan['controls']:
            a,b=[root/stem/('BRIDGE-'+tag+'-'+arm) for tag in ('OLD','NEW')]
            ra=command_check(root,a,plan,spec,arm,13630003,5102,old=True);rb=command_check(root,b,plan,spec,arm,13630003,5102)
            assert ra['paidSHA256']==rb['paidSHA256'] and initial_key(a)==initial_key(b)
            assert endpoint(a,'FE',5102)['front']==endpoint(b,'FE',5102)['front']


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert read(root/'status.json')['status']=='COMPLETE' and read(root/'bridge-acceptance.json')['passed']
    assert protected()==protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/PA_ROLE_SCHEDULE_PILOT_V1.json')==protocol['contractSHA256']
    assert digest(Path(plan['engineeringRoot'])/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    hashes=read(root/'class-hashes.json');assert class_hashes(root/'classes')==hashes['wrapper'] and class_hashes(root/'kernel-classes')==hashes['kernel']
    cp=(root/'classpath.txt').read_text().strip()
    for name,value in read(root/'inherited-identities.json').items():assert resolve_class(cp,name)==value
    bridges(root,plan);instances=[]
    for spec,item in zip(plan['instances'],result['instances']):
        stem=spec['stem'];assert item['instance']==stem
        for name,sha in read(root/stem/'input-hashes.json').items():assert digest(root/stem/'inputs'/name)==sha
        for seed in plan['seeds']:
            initial=None
            for arm in plan['arms']:
                folder=root/stem/str(seed)/('FE-'+arm);r=command_check(root,folder,plan,spec,arm,seed,spec['fixedFE'])
                observation,=[v for v in item['observations'] if v['seed']==seed and v['arm']==arm]
                assert observation['successfulFE']==r['successful'] and observation['searchSeconds']==r['searchSeconds'] and observation['stageFE']==r['search']
                current=initial_key(folder)
                if initial is None:initial=current
                assert len(current)==100 and current==initial
        instances.append(metric_audit(root,item,spec,plan))
    totals=counts(root);assert totals['runs']==84 and totals['successfulFE']==totals['attemptedFE']==plan['plannedTotalAttemptedFE']
    assert totals['failedFE']==totals['timeInterruptedAttempts']==0 and totals['attemptedFE']<=plan['maximumTotalAttemptedFE']
    for key,value in totals.items():assert result[key]==value
    assert result['pass_']==all(v['pass_'] for v in instances)
    expected='ORDINARY_BASE_SIGNAL_ONLY_SEPARATE_INTEGRATION_REQUIRED' if result['pass_'] else 'STOP_FIXED_OBJECTIVE_ROLE_AND_VISIT_FULL'
    assert result['decision']==expected
    write_once(root/'independent-final-audit.json',dict(passed=True,instances=instances,**totals,allIndicatorsCountsCriteriaAndInitialsVerified=True,
        allRoleMappingsAndBridgesVerified=True,newSearchFE=0,newDecoderCalls=0,defaultMainlineChanged=False,goalAchieved=False))
    folder=root/'independent-audit-source';folder.mkdir()
    for name in (Path(__file__).name,'pa_role_pilot_metric_audit.py'):shutil.copy2(Path(__file__).with_name(name),folder)
    print('PA_ROLE_PILOT_FINAL_AUDIT_PASS',totals,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

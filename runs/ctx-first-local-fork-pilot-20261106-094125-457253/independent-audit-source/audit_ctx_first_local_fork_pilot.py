"""Independent paired indicators, strict budgets, initial equality, flags and bridge rechecks."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
import shutil
import sys
from collections import Counter
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from ctx_gom_capability_support import counts,checked
from qpa_capability_analysis import endpoint
from pa_capability_support import initial_key
from ctx_gom_replay import raw_hash
from audit_pa_qpa_complement_capacity import independent_nd,coverage
from audit_qpa_completed_donor_pilot import scalar_metrics,criterion,flags


def command_check(folder,plan,spec,arm,seed,mode,old=False):
    template=Path(plan['source'])/spec['stem']/'14910003'/('FE500K-'+arm)
    actual,original=read(folder/'command.json'),read(template/'command.json')
    vm,settings=flags(actual);oldvm,oldsettings=flags(original);assert vm==oldvm
    assert settings==dict(oldsettings,**{'research.ctxFork.localInput':mode,'research.pa.auditPaid':'true'})
    entry='research.dynamic.GomCapabilityRun' if old else 'research.dynamic.GomForkCapabilityRun';at=actual.index(entry)
    assert actual[at+5:]==[arm,str(5102 if folder.name.startswith('BRIDGE-OLD') or folder.name.startswith('BRIDGE-NEW') else spec['fixedFE']),str(seed),'Infinity']
    assert Path(actual[at+4])==folder
    return actual[actual.index('-cp')+1]


def check_fork(folder,arm,mode,receipt):
    helper=read(folder/'fork-input.json');cp=read(folder/'command.json');cp=cp[cp.index('-cp')+1]
    verify_capture(helper['identity'],cp);fork=helper['fork']
    if arm not in ('SHARE_CTX_GOM','UNIFORM_CTX_GOM','SYNC_CTX_GOM'):
        assert fork['cyclesStarted']==fork['snapshotChecks']==0;return
    assert fork['mode']==mode and fork['snapshotChecks']==(100 if mode=='PRE_FIRST' else 0)
    assert [e['source'] for e in fork['entries']]==(['PRE','POST'] if mode=='PRE_FIRST' else ['POST','POST'])
    assert receipt['search']['contextGom']['completePasses']==2
    initial=rows(folder/'initial-population.jsonl')
    assert Counter(p['rawSHA256'] for p in fork['entries'][0]['before'])==Counter(raw_hash(p) for p in initial)
    for event in fork['entries']:
        for cohort in ('before','global','local'):
            assert Counter(p['family'] for p in event[cohort])==Counter({-1:80,0:5,1:5,2:5,3:5})
            assert len(event[cohort])==100 and all(raw_hash(p)==p['rawSHA256'] for p in event[cohort])
        assert event['local']==event['before' if event['source']=='PRE' else 'global']


def audit_instance(root,item,spec,plan):
    stem,norm=spec['stem'],spec['normalization'];fronts={};values={};initials={};errors=[]
    for observation in item['observations']:
        seed,arm=observation['seed'],observation['arm'];real,mode=plan['armDefinitions'][arm]
        folder=root/stem/str(seed)/('FE-'+arm);cp=command_check(folder,plan,spec,real,seed,mode)
        receipt=checked(folder,cp,spec['fixedFE'],float('inf'))
        assert receipt['successful']==receipt['attempted']==receipt['decoder']['dynamic.evaluations']==spec['fixedFE']
        assert observation['successfulFE']==receipt['successful'] and observation['searchSeconds']==receipt['searchSeconds']
        assert observation['stageFE']==receipt['search']
        current=initial_key(folder);assert len(current)==100
        if seed not in initials:initials[seed]=current
        assert current==initials[seed]
        check_fork(folder,real,mode,receipt)
        front=independent_nd(endpoint(folder,'FE',spec['fixedFE'])['front'])
        assert np.array_equal(front,np.array(observation['metrics']['front']))
        fronts[seed,arm]=front;values[seed,arm]=observation['metrics']
    assert set(fronts)=={(s,a) for s in plan['seeds'] for a in plan['arms']}
    for seed in plan['seeds']:
        for a,b in (('PRE_S','POST_S'),('PRE_U','POST_U')):
            pre=read(root/stem/str(seed)/('FE-'+a)/'fork-input.json')['fork']['entries'][0]
            post=read(root/stem/str(seed)/('FE-'+b)/'fork-input.json')['fork']['entries'][0]
            assert pre['before']==post['before'] and pre['global']==post['global']
    reference=independent_nd(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    assert np.array_equal(reference,np.array(item['reference']))
    for key,front in fronts.items():
        hv,igd=scalar_metrics(front,reference,norm);value=values[key]
        error=max(abs(hv[r]-value['HV'][r]) for r in hv);ie=abs(igd-value['IGDplus'])
        assert error<2e-11 and ie<2e-12;errors.append(dict(seed=key[0],arm=key[1],HVError=error,IGDplusError=ie))
    assert {r['B'] for r in item['comparisons']}==set(plan['criterionByControl'])
    for row in item['comparisons']:
        assert row['A']==plan['primary'] and row['kind']==plan['criterionByControl'][row['B']]
        effects={r:[] for r in ('1.25','1.5','2.0')};igds=[];deltas=[]
        for pair in row['pairs']:
            seed=pair['seed'];a,b=fronts[seed,row['A']],fronts[seed,row['B']];c=pair['coverage']
            assert c['coveredB']==coverage(a,b) and c['coveredA']==coverage(b,a)
            assert c['totalA']==len(a) and c['totalB']==len(b)
            assert c['C_A_B']==c['coveredB']/len(b) and c['C_B_A']==c['coveredA']/len(a)
            assert c['sharedObjectiveVectors']==len(set(map(tuple,a))&set(map(tuple,b)))
            av,bv=values[seed,row['A']],values[seed,row['B']]
            for r in effects:
                effect=100*(av['HV'][r]/bv['HV'][r]-1);assert effect==pair['HVEffectPct'][r];effects[r].append(effect)
            den=av['IGDplus']+bv['IGDplus'];igd=200*(av['IGDplus']-bv['IGDplus'])/den if den else 0.
            delta=c['C_A_B']-c['C_B_A'];assert igd==pair['IGDplusSymmetricWorseningPct'] and delta==pair['Cdelta']
            igds.append(igd);deltas.append(delta)
        assert row['medianHVEffectPct']=={r:float(np.median(v)) for r,v in effects.items()}
        assert row['medianIGDplusSymmetricWorseningPct']==float(np.median(igds)) and row['medianCdelta']==float(np.median(deltas))
        for key in ('C_A_B','C_B_A'):assert row['median'+key]==float(np.median([p['coverage'][key] for p in row['pairs']]))
        checks=criterion(row,plan['criteria'][row['kind']]);assert row['registeredAssessment']==dict(checks=checks,pass_=all(checks.values()))
    assert item['pass_']==all(r['registeredAssessment']['pass_'] for r in item['comparisons'])
    return dict(instance=stem,indicators=errors,pass_=item['pass_'],initialAndFirstGlobalStatesMatched=True)


def bridges(root,plan):
    engine=Path(plan['engineeringRoot'])
    for spec in plan['instances']:
        stem=spec['stem']
        for arm in ('SHARE_CTX_GOM','UNIFORM_CTX_GOM'):
            for mode in ('POST','PRE_FIRST'):
                folder=root/stem/('BRIDGE-'+arm+'-'+mode);cp=command_check(folder,plan,spec,arm,14810003,mode)
                receipt=checked(folder,cp,spec['fixedFE'],float('inf'));native,=rows(engine/stem/(arm+'-'+mode)/'receipt.jsonl')
                assert receipt['paidSHA256']==native['paidSHA256']
                assert sorted(map(tuple,endpoint(folder,'FE',spec['fixedFE'])['front']))==sorted(tuple(p['objectives']) for p in native['lastValidFront'])
        for arm in ('FULL_SHARED_DEEP','LI_RECON_DEEP'):
            records=[]
            for tag in ('OLD','NEW'):
                folder=root/stem/('BRIDGE-'+tag+'-'+arm);cp=command_check(folder,plan,spec,arm,14810003,'POST',old=tag=='OLD')
                records.append(checked(folder,cp,5102,float('inf')))
            assert records[0]['paidSHA256']==records[1]['paidSHA256']


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert read(root/'status.json')['status']=='COMPLETE' and read(root/'bridge-acceptance.json')['passed']
    assert protected()==protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/CTX_FIRST_LOCAL_FORK_PILOT_V1.json')==protocol['contractSHA256']
    assert digest(Path(plan['engineeringRoot'])/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    for directory,manifest in (('source','source-hashes.json'),('kernel-source','kernel-source-hashes.json')):
        for name,sha in read(root/manifest).items():assert digest(root/directory/name)==sha
    hashes=read(root/'class-hashes.json');assert class_hashes(root/'classes')==hashes['wrapper'] and class_hashes(root/'kernel-classes')==hashes['kernel']
    for spec in plan['instances']:
        for name,sha in read(root/spec['stem']/'input-hashes.json').items():assert digest(root/spec['stem']/'inputs'/name)==sha
    bridges(root,plan)
    instances=[audit_instance(root,item,spec,plan) for item,spec in zip(result['instances'],plan['instances'])]
    actual=counts(root);assert actual['runs']==52 and actual['successfulFE']==actual['attemptedFE']==plan['plannedTotalAttemptedFE']
    assert actual['failedFE']==actual['timeInterruptedAttempts']==0 and actual['attemptedFE']<=plan['maximumTotalAttemptedFE']
    assert result['pass_']==all(i['pass_'] for i in instances)
    for key,value in actual.items():assert result[key]==value
    write_once(root/'independent-final-audit.json',dict(passed=True,instances=instances,**actual,
        allIndicatorsCountsCriteriaAndInitialsIndependentlyVerified=True,allBridgesRechecked=True,newSearchFE=0,newDecoderCalls=0,goalAchieved=False))
    folder=root/'independent-audit-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('CTX_FIRST_LOCAL_FORK_PILOT_INDEPENDENT_AUDIT_PASS',actual,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

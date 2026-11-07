"""Independent reference, indicators, source flags, class identity and strict-FE acceptance."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
import shutil
import sys
import numpy as np

from run_long_budget_bridge import read,rows,write_once
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from research.expansion_audit.metrics import grid_hv
from audit_pa_qpa_complement_capacity import independent_nd,coverage
from pa_capability_support import initial_key
from qpa_capability_analysis import endpoint
from ctx_gom_capability_support import counts,checked


def flags(command):
    prefix=command[1:command.index('-cp')];properties={}
    for value in prefix:
        if value.startswith('-D'):
            key,setting=value[2:].split('=',1);assert key not in properties;properties[key]=setting
    return [v for v in prefix if not v.startswith('-D')],properties


def check_command(folder,plan,arm,seed):
    context=arm=='NSGA_CTX_GOM';source=Path(plan['sourceCtx'] if context else plan['sourceQpa'])
    underlying='QPA_DIRECT' if arm in ('ALL','OWN','SYNC') else arm
    stem=folder.parents[1].name;old=read(source/stem/str(14910003 if context else 14730003)/('FE500K-'+underlying)/'command.json')
    new=read(folder/'command.json');oldvm,oldflags=flags(old);newvm,newflags=flags(new);assert oldvm==newvm
    expected=dict(oldflags,**{'research.pa.auditPaid':'true','research.pa.traceIdentity':'false','research.qpa.completedDonors':arm if arm in ('ALL','OWN','SYNC') else 'SYNC'})
    assert newflags==expected
    entry='research.dynamic.GomCapabilityRun' if context else 'research.dynamic.QpaFeedbackCapabilityRun';at=new.index(entry)
    assert new[at+5:]==[underlying,str(plan['fixedFE']),str(seed),'Infinity'] and Path(new[at+4])==folder
    return new[new.index('-cp')+1],underlying


def scalar_metrics(front,reference,norm):
    normal=(front-norm['lower'])/norm['scale']
    igd=float(np.mean([np.sqrt(np.sum(np.maximum(normal-r,0.)**2,axis=1)).min() for r in reference]))
    return {str(r):grid_hv(normal,r) for r in (1.25,1.5,2.)},igd


def criterion(row,spec):
    med=row['medianHVEffectPct'];pairs=row['pairs']
    return dict(medianHV=med['1.5']>=spec['medianHVEffectPct'],
        referenceSensitivity=med['1.25']>=spec['referenceHVEffectFloor'] and med['2.0']>=spec['referenceHVEffectFloor'],
        medianIGDplus=row['medianIGDplusSymmetricWorseningPct']<=spec['medianIGDSymmetricWorseningPct'],
        medianCdelta=row['medianCdelta']>=spec['medianCdelta'],
        seedHV=min(p['HVEffectPct']['1.5'] for p in pairs)>=spec['seedHVEffectFloor'],
        seedIGDplus=max(p['IGDplusSymmetricWorseningPct'] for p in pairs)<=spec['seedIGDWorseningCeiling'],
        seedCdelta=min(p['Cdelta'] for p in pairs)>=spec['seedCdeltaFloor'])


def audit_instance(root,item,plan):
    stem=item['instance'];norm=item['normalization'];fronts={};values={};metric_checks=[];initials={}
    for observation in item['observations']:
        seed,arm=observation['seed'],observation['arm'];folder=root/stem/str(seed)/('FE100K-'+arm)
        cp,real=check_command(folder,plan,arm,seed);receipt=checked(folder,cp,plan['fixedFE'],float('inf'))
        assert receipt['seed']==seed and receipt['arm']==real
        assert receipt['decoder']['dynamic.evaluations']==receipt['attempted']==receipt['successful']==plan['fixedFE']
        assert receipt['paidSHA256'] is not None and observation['successfulFE']==receipt['successful']
        current=initial_key(folder)
        if seed not in initials:initials[seed]=current
        assert current==initials[seed] and len(current)==100
        actual=np.array(endpoint(folder,'FE100K',plan['fixedFE'])['front']);expected=np.array(observation['metrics']['front'])
        assert np.array_equal(independent_nd(actual),expected);fronts[seed,arm]=expected;values[seed,arm]=observation['metrics']
        if arm!='NSGA_CTX_GOM':
            helper,=rows(folder/'completed-donor-identity.jsonl');verify_capture(helper['identity'],cp)
            if arm=='ALL':assert helper['reads']['crossRoleFreshMaskReads']>0
            elif arm=='OWN':assert helper['reads']['freshMaskReads']>0 and helper['reads']['crossRoleFreshMaskReads']==0
            elif arm=='SYNC':assert helper['reads']['freshMaskReads']==0
            else:assert helper['reads']['maskReads']==0
    reference=independent_nd(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    assert np.array_equal(reference,np.array(item['reference']))
    for key,front in fronts.items():
        hv,igd=scalar_metrics(front,reference,norm);value=values[key]
        hv_error=max(abs(hv[r]-value['HV'][r]) for r in hv);igd_error=abs(igd-value['IGDplus'])
        assert hv_error<2e-11 and igd_error<2e-12
        metric_checks.append(dict(seed=key[0],arm=key[1],independentHVError=hv_error,independentIGDplusError=igd_error))
    for row in item['comparisons']:
        assert row['kind']==plan['criterionByControl'][row['B']]
        effects={r:[] for r in ('1.25','1.5','2.0')};igds=[];deltas=[]
        for pair in row['pairs']:
            seed=pair['seed'];a,b=fronts[seed,'ALL'],fronts[seed,row['B']];c=pair['coverage']
            assert c['coveredB']==coverage(a,b) and c['coveredA']==coverage(b,a)
            assert c['totalA']==len(a) and c['totalB']==len(b)
            assert c['C_A_B']==c['coveredB']/len(b) and c['C_B_A']==c['coveredA']/len(a)
            assert c['sharedObjectiveVectors']==len(set(map(tuple,a))&set(map(tuple,b)))
            av,bv=values[seed,'ALL'],values[seed,row['B']]
            for r in effects:
                effect=100*(av['HV'][r]/bv['HV'][r]-1);assert effect==pair['HVEffectPct'][r];effects[r].append(effect)
            denominator=av['IGDplus']+bv['IGDplus'];igd=200*(av['IGDplus']-bv['IGDplus'])/denominator if denominator else 0.
            assert igd==pair['IGDplusSymmetricWorseningPct'];igds.append(igd)
            cd=c['C_A_B']-c['C_B_A'];assert cd==pair['Cdelta'];deltas.append(cd)
        assert {r:float(np.median(v)) for r,v in effects.items()}==row['medianHVEffectPct']
        assert float(np.median(igds))==row['medianIGDplusSymmetricWorseningPct'] and float(np.median(deltas))==row['medianCdelta']
        checks=criterion(row,plan['criteria'][row['kind']]);assert checks==row['registeredAssessment']['checks']
        assert all(checks.values())==row['registeredAssessment']['pass_']
    assert item['pass_']==all(r['registeredAssessment']['pass_'] for r in item['comparisons'])
    return dict(instance=stem,referenceSize=len(reference),observations=len(fronts),comparisons=len(item['comparisons']),metrics=metric_checks,pass_=item['pass_'])


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert read(root/'status.json')['status']=='COMPLETE' and read(root/'bridge-acceptance.json')['passed']
    assert protected()==protocol['protectedBefore']
    assert digest(Path('src/algorithms/model_global/qpa/QpaPopulation.java'))==protocol['originalQpaPopulationSHA256']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    for name,sha in read(root/'kernel-source-hashes.json').items():assert digest(root/'kernel-source'/name)==sha
    classes=read(root/'class-hashes.json');assert class_hashes(root/'classes')==classes['wrapper'] and class_hashes(root/'kernel-classes')==classes['kernel']
    for spec in plan['instances']:
        for name,sha in read(root/spec['stem']/'input-hashes.json').items():assert digest(root/spec['stem']/'inputs'/name)==sha
    checked_instances=[audit_instance(root,item,plan) for item in result['instances']]
    actual=counts(root);assert actual['successfulFE']==actual['attemptedFE']==plan['plannedBridgeFE']+plan['plannedScientificFE']
    assert actual['failedFE']==actual['timeInterruptedAttempts']==0 and actual['runs']==38
    assert result['qualificationPass']==all(i['pass_'] for i in checked_instances)
    for key,value in actual.items():assert result[key]==value
    record=dict(passed=True,instances=checked_instances,**actual,exactInitialsFlagsPhysicsFEAndCriteriaVerified=True,
        referenceAndHVIGDplusCoverageIndependentlyVerified=True,newSearchFE=0,newDecoderCalls=0,goalAchieved=False)
    write_once(root/'independent-final-audit.json',record)
    destination=root/'independent-audit-source';destination.mkdir();shutil.copy2(Path(__file__),destination)
    print('QPA_DONOR_PILOT_INDEPENDENT_AUDIT_PASS',actual,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

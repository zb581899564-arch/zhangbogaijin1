"""Independent saved-front union, alternate-axis HV, scalar IGD/C and stop-rule checks."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from pathlib import Path
import sys
import shutil
import numpy as np

from run_long_budget_bridge import read,write_once
from qpa_capability_analysis import endpoint
from research.expansion_audit.metrics import grid_hv
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected


def independent_nd(points):
    unique=np.array(sorted(set(map(tuple,points))),dtype=float);keep=[]
    for start in range(0,len(unique),64):
        x=unique[start:start+64]
        dominated=(np.all(unique[None,:,:]<=x[:,None,:],axis=2)&np.any(unique[None,:,:]<x[:,None,:],axis=2)).any(axis=1)
        keep.extend(x[~dominated].tolist())
    return np.array(keep)


def metrics(front,reference,norm):
    normal=(front-norm['lower'])/norm['scale']
    igd=float(np.mean([np.sqrt(np.sum(np.maximum(normal-r,0.)**2,axis=1)).min() for r in reference]))
    return {str(r):grid_hv(normal,r) for r in (1.25,1.5,2.)},igd


def coverage(a,b):
    return sum(np.all(a<=y,axis=1).any() for y in b)


def criterion(row,improvement):
    hv=row['medianHVEffectPct'];pairs=row['pairs'];igd=row['medianIGDplusSymmetricWorseningPct']
    cd=[p['coverage']['C_A_B']-p['coverage']['C_B_A'] for p in pairs]
    return dict(medianHV=hv['1.5']>=(1. if improvement else -1.),
        sensitivity=min(hv['1.25'],hv['2.0'])>=(0. if improvement else -1.),
        medianIGDplus=igd<=(0. if improvement else 5.),medianC=float(np.median(cd))>=(0. if improvement else -.02),
        seedHV=all(p['HVEffectPct']['1.5']>=(-1. if improvement else -3.) for p in pairs),
        seedIGDplus=all(p['IGDplusSymmetricWorseningPct']<=(5. if improvement else 10.) for p in pairs),
        seedC=min(cd)>=(-.02 if improvement else -.05))


def audit_instance(item,source,plan):
    stem=item['instance'];norm=item['normalization'];seeds=plan['seeds'];values={};fronts={};half={}
    for seed in seeds:
        for arm in plan['arms']:
            folder=source/stem/str(seed)/('FE500K-'+arm)
            fronts[seed,arm]=np.array(endpoint(folder,'FE500K',500000)['front'])
            if arm in ('PA_JOINT','QPA_DIRECT','PA_EQUAL'):
                half[seed,arm]=np.array(endpoint(folder,'FE500K',250000)['front'])
                assert coverage(fronts[seed,arm],half[seed,arm])==len(half[seed,arm])
    reference=independent_nd(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    assert np.array_equal(reference,np.array(item['reference']))
    for index,seed in enumerate(seeds):
        other=seeds[1-index]
        fronts[seed,'MIX_ORACLE']=independent_nd(np.vstack([half[seed,'PA_JOINT'],half[other,'QPA_DIRECT']]))
        for arm in ('PA_JOINT','QPA_DIRECT','PA_EQUAL'):
            fronts[seed,'RESTART_'+arm]=independent_nd(np.vstack([half[seed,arm],half[other,arm]]))
    maximum_hv=0.;maximum_igd=0.
    cached={}
    for observation in item['observations']:
        key=observation['seed'],observation['arm'];actual=np.array(observation['front']);assert np.array_equal(actual,fronts[key])
        physical=tuple(map(tuple,actual))
        if physical not in cached:cached[physical]=metrics(actual,reference,norm)
        hv,igd=cached[physical];record=observation['metrics'];values[key]=record
        for r in hv:
            error=abs(hv[r]-record['HV'][r]);assert error<2e-11;maximum_hv=max(maximum_hv,error)
        error=abs(igd-record['IGDplus']);assert error<2e-12;maximum_igd=max(maximum_igd,error)
    for row in item['comparisons']:
        effects={r:[] for r in ('1.25','1.5','2.0')};igds=[]
        for pair in row['pairs']:
            seed=pair['seed'];a=fronts[seed,'MIX_ORACLE'];b=fronts[seed,row['B']];c=pair['coverage']
            assert c['coveredB']==coverage(a,b) and c['coveredA']==coverage(b,a)
            assert c['totalA']==len(a) and c['totalB']==len(b)
            assert c['C_A_B']==c['coveredB']/len(b) and c['C_B_A']==c['coveredA']/len(a)
            av,bv=values[seed,'MIX_ORACLE'],values[seed,row['B']]
            for r in effects:
                effect=100*(av['HV'][r]/bv['HV'][r]-1);assert effect==pair['HVEffectPct'][r];effects[r].append(effect)
            denominator=av['IGDplus']+bv['IGDplus'];effect=200*(av['IGDplus']-bv['IGDplus'])/denominator if denominator else 0.
            assert effect==pair['IGDplusSymmetricWorseningPct'];igds.append(effect)
        assert {r:float(np.median(p)) for r,p in effects.items()}==row['medianHVEffectPct']
        assert float(np.median(igds))==row['medianIGDplusSymmetricWorseningPct']
        expected=criterion(row,row['B'] in ('RESTART_PA_JOINT','RESTART_QPA_DIRECT'))
        assert expected==row['capacityAssessment']['checks'] and all(expected.values())==row['capacityAssessment']['pass_']
    assert item['pass_']==all(r['capacityAssessment']['pass_'] for r in item['comparisons'])
    return dict(instance=stem,frontsChecked=len(fronts),comparisonsChecked=len(item['comparisons']),
        maxHVerror=maximum_hv,maxIGDplusError=maximum_igd,pass_=item['pass_'])


def audit(root):
    protocol=read(root/'protocol.json');result=read(root/'analysis.json');source=Path(protocol['source']);plan=read(source/'protocol.json')
    assert protected()==protocol['protectedBefore'] and digest(source/'fe500k-analysis.json')==protocol['sourceAnalysisSHA256']
    assert digest(source/'post-audit.json')==protocol['sourceAuditSHA256']
    for item in result['instances']:
        for folder,hashes in read(root/(item['instance']+'-source-identities.json')).items():
            for name,sha in hashes.items():assert digest(Path(folder)/name)==sha
    checked=[audit_instance(item,source,plan) for item in result['instances']]
    assert result['pass_']==all(item['pass_'] for item in checked)==False
    assert result['decision']=='STOP_FIXED_INDEPENDENT_PA_QPA_HALF_BUDGET_POOLING'
    proof=dict(passed=True,instances=checked,source500kQualificationUnchanged=True,initialAndPaidArtifactsUnchanged=True,
        unionAndReferenceIndependentlyReconstructed=True,coverageCountsAndGateChecksEqual=True,newSearchFE=0,newDecoderCalls=0,
        independenceWarningPreserved=True,defaultMainlineChanged=False,goalAchieved=False)
    write_once(root/'independent-final-audit.json',proof)
    directory=root/'independent-audit-source';directory.mkdir();shutil.copy2(Path(__file__),directory)
    print('PA_QPA_CAPACITY_INDEPENDENT_AUDIT_PASS',checked,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())

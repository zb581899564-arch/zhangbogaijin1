"""Independent scalar metrics, weak coverage counts, effects and frozen decision."""
import numpy as np

from qpa_capability_analysis import endpoint
from audit_pa_qpa_complement_capacity import independent_nd,coverage
from audit_qpa_completed_donor_pilot import scalar_metrics,criterion


def compare(row,values,fronts,plan):
    assert row['A']==plan['primary'] and row['kind']==plan['criterionByControl'][row['B']]
    assert [p['seed'] for p in row['pairs']]==plan['seeds']
    effects={r:[] for r in ('1.25','1.5','2.0')};igds=[];deltas=[]
    for pair in row['pairs']:
        seed=pair['seed'];a,b=fronts[seed,row['A']],fronts[seed,row['B']];c=pair['coverage']
        assert c['coveredB']==coverage(a,b) and c['coveredA']==coverage(b,a)
        assert c['totalA']==len(a) and c['totalB']==len(b)
        assert c['C_A_B']==c['coveredB']/len(b) and c['C_B_A']==c['coveredA']/len(a)
        assert c['sharedObjectiveVectors']==len(set(map(tuple,a))&set(map(tuple,b)))
        av,bv=values[seed,row['A']],values[seed,row['B']]
        for r in effects:
            value=100*(av['HV'][r]/bv['HV'][r]-1);assert value==pair['HVEffectPct'][r];effects[r].append(value)
        den=av['IGDplus']+bv['IGDplus'];igd=200*(av['IGDplus']-bv['IGDplus'])/den if den else 0.
        delta=c['C_A_B']-c['C_B_A'];assert igd==pair['IGDplusSymmetricWorseningPct'] and delta==pair['Cdelta']
        igds.append(igd);deltas.append(delta)
    assert row['medianHVEffectPct']=={r:float(np.median(v)) for r,v in effects.items()}
    assert row['medianIGDplusSymmetricWorseningPct']==float(np.median(igds)) and row['medianCdelta']==float(np.median(deltas))
    for key in ('C_A_B','C_B_A'):assert row['median'+key]==float(np.median([p['coverage'][key] for p in row['pairs']]))
    checks=criterion(row,plan['criteria'][row['kind']]);assert row['registeredAssessment']==dict(checks=checks,pass_=all(checks.values()))


def verify(root,item,spec,plan):
    fronts={};values={};norm=spec['normalization'];errors=[]
    for row in item['observations']:
        key=row['seed'],row['arm'];folder=root/spec['stem']/str(key[0])/('FE-'+key[1])
        front=independent_nd(endpoint(folder,'FE',spec['fixedFE'])['front'])
        assert np.array_equal(front,np.array(row['metrics']['front']));fronts[key]=front;values[key]=row['metrics']
    assert set(fronts)=={(s,a) for s in plan['seeds'] for a in plan['arms']}
    reference=independent_nd(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    assert np.array_equal(reference,np.array(item['reference']))
    for key,front in fronts.items():
        hv,igd=scalar_metrics(front,reference,norm);value=values[key]
        error=max(abs(hv[r]-value['HV'][r]) for r in hv);ie=abs(igd-value['IGDplus'])
        assert error<2e-11 and ie<2e-12;errors.append(dict(seed=key[0],arm=key[1],HVError=error,IGDplusError=ie))
    assert {r['B'] for r in item['comparisons']}==set(plan['criterionByControl'])
    for row in item['comparisons']:compare(row,values,fronts,plan)
    assert item['pass_']==all(r['registeredAssessment']['pass_'] for r in item['comparisons'])
    return dict(instance=spec['stem'],indicatorErrors=errors,pass_=item['pass_'])

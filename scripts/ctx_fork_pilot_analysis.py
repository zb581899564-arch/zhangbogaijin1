"""Fixed short-horizon ancestry pilot; all three indicators and all registered controls."""
import numpy as np

from run_long_budget_bridge import rows,write_once,nondominated
from qpa_capability_analysis import endpoint
from ctx_phase_analysis import metric,paired
from qpa_feedback_pilot_analysis import assessment


def instance(root,spec,plan):
    stem,norm=spec['stem'],spec['normalization'];folders={(s,a):root/stem/str(s)/('FE-'+a) for s in plan['seeds'] for a in plan['arms']}
    fronts={key:np.array(endpoint(folder,'FE',spec['fixedFE'])['front']) for key,folder in folders.items()}
    reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    values={key:metric(front,norm,reference) for key,front in fronts.items()};observations=[]
    for (seed,arm),value in values.items():
        r,=rows(folders[seed,arm]/'run-receipt.jsonl')
        observations.append(dict(seed=seed,arm=arm,metrics=value,searchSeconds=r['searchSeconds'],successfulFE=r['successful'],stageFE=r['search']))
    comparisons=[]
    for opponent,kind in plan['criterionByControl'].items():
        pairs=[dict(seed=s,**paired(values[s,plan['primary']],values[s,opponent])) for s in plan['seeds']]
        row=dict(A=plan['primary'],B=opponent,kind=kind,pairs=pairs,
            medianHVEffectPct={str(r):float(np.median([p['HVEffectPct'][str(r)] for p in pairs])) for r in (1.25,1.5,2.)},
            medianIGDplusSymmetricWorseningPct=float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs])),
            medianCdelta=float(np.median([p['Cdelta'] for p in pairs])),
            medianC_A_B=float(np.median([p['coverage']['C_A_B'] for p in pairs])),medianC_B_A=float(np.median([p['coverage']['C_B_A'] for p in pairs])))
        row['registeredAssessment']=assessment(row,plan['criteria'][kind]);comparisons.append(row)
    return dict(instance=stem,normalization=norm,reference=reference.tolist(),observations=observations,comparisons=comparisons,
        pass_=all(c['registeredAssessment']['pass_'] for c in comparisons))


def analyze(root,plan,costs):
    cases=[instance(root,spec,plan) for spec in plan['instances']];passed=all(c['pass_'] for c in cases)
    result=dict(instances=cases,pass_=passed,**costs,
        decision='SHORT_HORIZON_SIGNAL_ONLY_SEPARATE_FULL_QUALIFICATION_REQUIRED' if passed else 'STOP_FIXED_FIRST_LOCAL_FORK',
        full500kAdvantageProved=False,sameTimeTested=False,defaultMainlineChanged=False,goalAchieved=False)
    write_once(root/'analysis.json',result);return result

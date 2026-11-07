"""Full ten-arm paired three-indicator qualification, independent role and sharing evidence."""
import numpy as np

from run_long_budget_bridge import rows, write_once, hypervolume, igd_plus, nondominated
from qpa_capability_analysis import endpoint, compare


def assessment(record,kind):
    hv = record['medianHVEffectPct']; igd = record['medianIGDplusSymmetricWorseningPct']
    cd = [p['coverage']['C_A_B']-p['coverage']['C_B_A'] for p in record['pairs']]
    if kind in ('improvement','mechanism'):
        checks = dict(medianHV=hv['1.5'] >= (1. if kind == 'improvement' else .5),
            sensitivity=min(hv['1.25'],hv['2.0']) >= 0,medianIGDplus=igd <= 0,medianC=float(np.median(cd)) >= 0,
            seedHV=all(p['HVEffectPct']['1.5'] >= -1 for p in record['pairs']),
            seedIGDplus=all(p['IGDplusSymmetricWorseningPct'] <= 5 for p in record['pairs']),seedC=min(cd) >= -.02)
    else:
        checks = dict(medianHV=hv['1.5'] >= -1,sensitivity=min(hv['1.25'],hv['2.0']) >= -1,
            medianIGDplus=igd <= 5,medianC=float(np.median(cd)) >= -.02,
            seedHV=all(p['HVEffectPct']['1.5'] >= -3 for p in record['pairs']),
            seedIGDplus=all(p['IGDplusSymmetricWorseningPct'] <= 10 for p in record['pairs']),seedC=min(cd) >= -.05)
    return dict(kind=kind,checks=checks,pass_=all(checks.values()))


def analyze(root,plan,phase):
    results = []
    for spec in plan['instances']:
        stem,norm = spec['stem'],spec['normalization']; limit = spec['time_seconds'] if phase == 'TIME' else plan['fixedFE']
        folders = {(seed,arm): root/stem/str(seed)/(phase+'-'+arm) for seed in plan['seeds'] for arm in plan['arms']}
        fronts = {key:np.asarray(endpoint(folder,phase,limit)['front'],float) for key,folder in folders.items()}
        normalized = {key:(p-norm['lower'])/norm['scale'] for key,p in fronts.items()}
        reference = nondominated(np.vstack(list(normalized.values()))); values = {}
        for key,front in normalized.items():
            receipt, = rows(folders[key]/'run-receipt.jsonl')
            values[key] = dict(seed=key[0],arm=key[1],frontSize=len(front),
                HV={str(r):hypervolume(front,(r,)*3) for r in (1.25,1.5,2.)},IGDplus=igd_plus(front,reference),
                objectiveMin=fronts[key].min(axis=0).tolist(),successfulFE=receipt['successful'],searchSeconds=receipt['searchSeconds'],
                stageFE=receipt['search'])
            assert min(values[key]['HV'].values()) > 1e-12, 'Unidentifiable HV ratio'
        comparisons = []
        for opponent in plan['arms'][1:]:
            record = compare('SHARE_CTX_GOM',opponent,plan['seeds'],values,fronts)
            kind = 'mechanism' if opponent in ('SYNC_CTX_GOM','UNIFORM_CTX_GOM') else 'improvement' if opponent in plan['improvementControls'] else 'noninferiority'
            record['registeredAssessment'] = assessment(record,kind); comparisons.append(record)
        comp = [p for p in comparisons if p['B'] not in ('SYNC_CTX_GOM','UNIFORM_CTX_GOM')]
        mech = [p for p in comparisons if p['B'] in ('SYNC_CTX_GOM','UNIFORM_CTX_GOM')]
        results.append(dict(stem=stem,referenceSize=len(reference),observations=list(values.values()),comparisons=comparisons,
            competitivePass=all(p['registeredAssessment']['pass_'] for p in comp),
            independentRoleAndSharingPass=all(p['registeredAssessment']['pass_'] for p in mech)))
    result = dict(phase=phase,instances=results,competitivePass=all(r['competitivePass'] for r in results),
        independentRoleAndSharingPass=all(r['independentRoleAndSharingPass'] for r in results),
        scope='Exploratory two development instances/two fresh seeds only; no heldout or novelty conclusion',goalAchieved=False)
    write_once(root/(phase.lower()+'-analysis.json'),result)
    return result

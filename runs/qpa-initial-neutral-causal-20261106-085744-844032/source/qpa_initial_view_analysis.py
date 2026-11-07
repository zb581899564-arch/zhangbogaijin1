"""Predeclared initial-view causal endpoint, jointly judging HV, IGD+ and both C directions."""
import numpy as np

from run_long_budget_bridge import rows, write_once, nondominated
from qpa_capability_analysis import endpoint
from ctx_phase_analysis import metric, paired
from qpa_feedback_pilot_analysis import assessment


def analyze_instance(root, spec, plan):
    stem, norm = spec['stem'], spec['normalization']
    folders = {(seed, arm): root/stem/str(seed)/('FE100K-'+arm) for seed in plan['seeds'] for arm in plan['arms']}
    fronts = {key: np.array(endpoint(folder, 'FE100K', plan['fixedFE'])['front']) for key, folder in folders.items()}
    reference = nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    values = {key: metric(p, norm, reference) for key, p in fronts.items()}
    observations = []
    for (seed, arm), value in values.items():
        receipt, = rows(folders[seed, arm]/'run-receipt.jsonl')
        observations.append(dict(seed=seed, arm=arm, metrics=value, searchSeconds=receipt['searchSeconds'], successfulFE=receipt['successful']))
    comparisons = []
    for opponent, kind in plan['criterionByControl'].items():
        pairs = [dict(seed=seed, **paired(values[seed, plan['primary']], values[seed, opponent])) for seed in plan['seeds']]
        row = dict(A=plan['primary'], B=opponent, kind=kind, pairs=pairs,
            medianHVEffectPct={str(r): float(np.median([p['HVEffectPct'][str(r)] for p in pairs])) for r in (1.25, 1.5, 2.)},
            medianIGDplusSymmetricWorseningPct=float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs])),
            medianCdelta=float(np.median([p['Cdelta'] for p in pairs])),
            medianC_A_B=float(np.median([p['coverage']['C_A_B'] for p in pairs])),
            medianC_B_A=float(np.median([p['coverage']['C_B_A'] for p in pairs])))
        row['registeredAssessment'] = assessment(row, plan['criteria'][kind])
        comparisons.append(row)
    return dict(instance=stem, normalization=norm, reference=reference.tolist(), observations=observations,
                comparisons=comparisons, pass_=all(r['registeredAssessment']['pass_'] for r in comparisons))


def analyze(root, plan, costs):
    instances = [analyze_instance(root, spec, plan) for spec in plan['instances']]
    passed = all(i['pass_'] for i in instances)
    result = dict(instances=instances, pass_=passed, **costs,
        decision='INITIAL_VIEW_CAUSAL_SIGNAL_ONLY_SEPARATE_INTEGRATION_REQUIRED' if passed else 'STOP_FIXED_INITIAL_CONCAT_PERFORMANCE_HYPOTHESIS',
        fullAlgorithmQualification=False, sameTimeTested=False, newFourRoleBenefitProved=False, defaultMainlineChanged=False, goalAchieved=False)
    write_once(root/'analysis.json', result)
    return result

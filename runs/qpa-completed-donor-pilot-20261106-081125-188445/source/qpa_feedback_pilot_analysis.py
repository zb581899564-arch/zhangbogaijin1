"""Prospective nine-arm joint indicators using the frozen numeric criteria."""
import csv
import numpy as np

from run_long_budget_bridge import rows,write_once,nondominated
from qpa_capability_analysis import endpoint
from ctx_phase_analysis import metric,paired


def assessment(record,thresholds):
    pairs=record['pairs'];hv=record['medianHVEffectPct']
    checks=dict(medianHV=hv['1.5']>=thresholds['medianHVEffectPct'],
        referenceSensitivity=min(hv['1.25'],hv['2.0'])>=thresholds['referenceHVEffectFloor'],
        medianIGDplus=record['medianIGDplusSymmetricWorseningPct']<=thresholds['medianIGDSymmetricWorseningPct'],
        medianCdelta=record['medianCdelta']>=thresholds['medianCdelta'],
        seedHV=all(p['HVEffectPct']['1.5']>=thresholds['seedHVEffectFloor'] for p in pairs),
        seedIGDplus=all(p['IGDplusSymmetricWorseningPct']<=thresholds['seedIGDWorseningCeiling'] for p in pairs),
        seedCdelta=all(p['Cdelta']>=thresholds['seedCdeltaFloor'] for p in pairs))
    return dict(checks=checks,pass_=all(checks.values()))


def analyze_instance(root,spec,plan):
    stem=spec['stem'];norm=spec['normalization'];values={};fronts={}
    for seed in plan['seeds']:
        for arm in plan['arms']:
            folder=root/stem/str(seed)/('FE100K-'+arm)
            fronts[seed,arm]=np.asarray(endpoint(folder,'FE100K',plan['fixedFE'])['front'])
    reference=nondominated(np.vstack([(p-norm['lower'])/norm['scale'] for p in fronts.values()]))
    observations=[]
    for (seed,arm),front in fronts.items():
        value=metric(front,norm,reference);values[seed,arm]=value
        receipt,=rows(root/stem/str(seed)/('FE100K-'+arm)/'run-receipt.jsonl')
        observations.append(dict(seed=seed,arm=arm,metrics=value,frontSize=len(value['front']),
            successfulFE=receipt['successful'],searchSeconds=receipt['searchSeconds'],
            stageFE={name:receipt['search'].get(name+'.evaluations',0) for name in ('initialization','global','inter','intra','jointLocal')}))
    comparisons=[]
    for opponent,kind in plan['criterionByControl'].items():
        pairs=[dict(seed=seed,**paired(values[seed,'ALL'],values[seed,opponent])) for seed in plan['seeds']]
        record=dict(A='ALL',B=opponent,kind=kind,pairs=pairs,
            medianHVEffectPct={str(r):float(np.median([p['HVEffectPct'][str(r)] for p in pairs])) for r in (1.25,1.5,2.)},
            medianIGDplusSymmetricWorseningPct=float(np.median([p['IGDplusSymmetricWorseningPct'] for p in pairs])),
            medianCdelta=float(np.median([p['Cdelta'] for p in pairs])),
            medianC_A_B=float(np.median([p['coverage']['C_A_B'] for p in pairs])),
            medianC_B_A=float(np.median([p['coverage']['C_B_A'] for p in pairs])))
        record['registeredAssessment']=assessment(record,plan['criteria'][kind]);comparisons.append(record)
    passed=lambda group:all(r['registeredAssessment']['pass_'] for r in comparisons if (r['B'] in ('OWN','SYNC'))==group)
    return dict(instance=stem,normalization=norm,reference=reference.tolist(),observations=observations,comparisons=comparisons,
        feedbackPass=passed(True),competitivePass=passed(False),pass_=all(r['registeredAssessment']['pass_'] for r in comparisons))


def analyze(root,plan,fees):
    instances=[analyze_instance(root,spec,plan) for spec in plan['instances']];passed=all(i['pass_'] for i in instances)
    result=dict(instances=instances,qualificationPass=passed,
        decision='PILOT_POSITIVE_SEPARATE_500K_AND_ROLE_PROTOCOL_REQUIRED' if passed else 'STOP_FIXED_COMPLETED_DONOR_ALL_PILOT',
        **fees,sameTimeTested=False,full500kAdvantageProved=False,fourRoleIndependentBenefitProved=False,defaultMainlineChanged=False,goalAchieved=False)
    write_once(root/'analysis.json',result)
    with (root/'observations.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        columns=('instance','seed','arm','successfulFE','searchSeconds','frontSize','HV1.25','HV1.5','HV2.0','IGDplus')
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for item in instances:
            for observation in item['observations']:
                writer.writerow(dict(instance=item['instance'],**{k:observation[k] for k in columns if k in observation},
                    **{'HV'+r:observation['metrics']['HV'][r] for r in ('1.25','1.5','2.0')},IGDplus=observation['metrics']['IGDplus']))
    return result

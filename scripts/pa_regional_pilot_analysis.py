"""Fixed regional-CENTER joint-indicator pilot, never selecting a winning control."""
import csv
from ctx_fork_pilot_analysis import instance
from run_long_budget_bridge import write_once


def analyze(root,plan,costs):
    cases=[instance(root,spec,plan) for spec in plan['instances']];passed=all(c['pass_'] for c in cases)
    result=dict(instances=cases,pass_=passed,**costs,
        decision='ORDINARY_REGIONAL_SIGNAL_ONLY_SEPARATE_INTEGRATION_REQUIRED' if passed else 'STOP_FIXED_REGIONAL_CENTER_PILOT',
        scope='Ordinary fixed-region foundation and extreme-preference ablation only; original QGS/fixed families/conditional sharing not integrated',
        full500kAdvantageProved=False,sameTimeTested=False,defaultMainlineChanged=False,goalAchieved=False)
    write_once(root/'analysis.json',result)
    with (root/'observations.csv').open('x',encoding='utf-8-sig',newline='') as stream:
        fields=('instance','seed','arm','successfulFE','searchSeconds','HV1.25','HV1.5','HV2.0','IGDplus');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for case in cases:
            for row in case['observations']:
                writer.writerow(dict(instance=case['instance'],seed=row['seed'],arm=row['arm'],successfulFE=row['successfulFE'],searchSeconds=row['searchSeconds'],
                    **{'HV'+r:row['metrics']['HV'][r] for r in ('1.25','1.5','2.0')},IGDplus=row['metrics']['IGDplus']))
    return result

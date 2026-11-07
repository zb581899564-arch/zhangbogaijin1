"""Descriptive interpretation of the complete single-order matrix; no extra evaluations."""
import json
from pathlib import Path
import sys
import pandas as pd

root=Path(sys.argv[1]).resolve();status=json.loads((root/'final-status.json').read_text())
assert status['status']=='CENTER_LAST_COMPLETE' and status['completed']==150
analysis=root/status['analysis'];effects=json.loads((analysis/'effects.json').read_text())
out=root/'interpretation';out.mkdir(exist_ok=False)
comparisons=[];instances=[]
for label,value in effects.items():
    time=value['T']['1.5'];fixed=value['FE15000']['allInstances'];lookup={r['instance']:r for r in fixed['instances']}
    comparisons.append({'comparison':label,'meanTPercent':time['mean_effect_percent'],'medianTPercent':time['median_effect_percent'],
        'practicalWins':time['practical_wins'],'practicalLosses':time['practical_losses'],'worstTPercent':time['worst_effect_percent'],
        'removeBestMeanTPercent':time['mean_after_removing_best_instance_percent'],'meanFE15000Percent':fixed['mean_effect_percent'],
        'reference1.25MeanPercent':value['T']['1.25']['mean_effect_percent'],'reference2.0MeanPercent':value['T']['2.0']['mean_effect_percent']})
    for row in time['instances']:
        instances.append({'comparison':label,'instance':row['instance'],'effectTPercent':row['effect_percent'],
                          'effectFE15000Percent':lookup[row['instance']]['effect_percent']})
pd.DataFrame(comparisons).to_csv(out/'comparison-summary.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(instances).to_csv(out/'instance-effects.csv',index=False,encoding='utf-8-sig')
compositions=pd.read_csv(analysis/'composition-run-metrics.csv')
for column,numerator,denominator in [
    ('sameGenerationFraction','sameGenerationFragments','selectedFragments'),
    ('sameGenerationLateGroupFraction','sameGenerationLateGroupFragments','selectedFragments'),
    ('archiveAdmissionEventRate','deadlineValidArchiveAdmissions','deadlineValidPaidAssemblies')]:
    compositions[column]=compositions[numerator]/compositions[denominator].where(compositions[denominator]>0)
fields=['eligibleCenterOpportunities','assemblyRequests','assembliesProposed','paidAssemblies','deadlineValidPaidAssemblies',
        'completeGenerations','sameGenerationFraction','sameGenerationLateGroupFraction','fragmentAgeFEMean','archiveAdmissionEventRate']
per_instance=compositions.groupby(['instance','variant'])[fields].mean().reset_index()
per_instance.to_csv(out/'composition-by-instance.csv',index=False,encoding='utf-8-sig')
per_instance.groupby('variant')[fields].mean().to_csv(out/'composition-summary.csv',encoding='utf-8-sig')
generations=pd.read_csv(analysis/'composition-generation-metrics.csv')
full=generations[generations.completeGeneration]
full.groupby(['instance','seed','variant'])[['eligibleCenterOpportunities','proposedAssemblies','paidAssemblies','validPaidAssemblies']].mean().reset_index().to_csv(
    out/'full-generation-composition.csv',index=False,encoding='utf-8-sig')
cost=pd.read_csv(analysis/'run-metrics.csv');cost['deadlineFEperSecond']=cost.deadlineValidFE/cost.searchSeconds
cost.groupby(['instance','variant'])[['deadlineFEperSecond','decodeSeconds']].mean().reset_index().to_csv(out/'costs-by-instance.csv',index=False,encoding='utf-8-sig')
previous=root.parent/'sync-job-audit-20261102-184848-424022';mapping={'SYNC_ORIGINAL':'SYNC_JOB','SHARE_ORIGINAL':'SHARE_JOB','NSGA':'NSGA'}
checked=[]
for path in (root/'trials/order').rglob('anytime.jsonl'):
    if path.parent.name not in mapping:continue
    stem=path.parents[2].name;seed=path.parents[1].name
    old=previous/'trials/audit'/stem/seed/mapping[path.parent.name]/'anytime.jsonl'
    def front(file):
        rows=[json.loads(line) for line in file.read_text().splitlines()]
        rows=[r for r in rows if r['checkpointKind']=='FE' and r['checkpoint']==15000]
        assert len(rows)==1 and rows[0].get('reached',True)
        return rows[0]['front']
    assert front(path)==front(old),str(path)
    checked.append(str(path.relative_to(root)))
assert len(checked)==90
(out/'control-fe-invariance.json').write_text(json.dumps({'status':'PASS','controls':90,'checkpoint':15000,'frontsExactlyEqual':True,'extraFE':0,'cells':checked},ensure_ascii=False,indent=2),encoding='utf-8')
audit=json.loads((analysis/'audit.json').read_text())
(out/'receipt.json').write_text(json.dumps(audit|{'mainCampaignSeconds':status['wallSeconds'],'postAnalysisExtraFE':0,'scope':'Single fixed order; no automatic enumeration or new mechanism'},ensure_ascii=False,indent=2),encoding='utf-8')
print(pd.DataFrame(comparisons).to_string(index=False));print('INTERPRETATION_COMPLETE',out)

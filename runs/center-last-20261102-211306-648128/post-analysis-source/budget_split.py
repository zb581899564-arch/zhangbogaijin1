"""Recompute full/partial-generation totals into an explicitly new output CSV."""
from pathlib import Path
import sys
import json
import pandas as pd

root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve()
analysis=root/json.loads((root/'final-status.json').read_text())['analysis']
generations=pd.read_csv(analysis/'composition-generation-metrics.csv')
totals=pd.read_csv(analysis/'composition-run-metrics.csv');keys=['instance','seed','variant'];result=totals[keys].copy()
for complete,name in [(True,'full'),(False,'partial')]:
    values=generations[generations.completeGeneration==complete].groupby(keys)[['eligibleCenterOpportunities','paidAssemblies']].sum().reset_index()
    values=values.rename(columns={'eligibleCenterOpportunities':name+'Opportunities','paidAssemblies':name+'PaidAssemblies'})
    result=result.merge(values,on=keys,how='left',validate='one_to_one')
    columns=[name+'Opportunities',name+'PaidAssemblies'];result[columns]=result[columns].fillna(0)
with output.open('x',encoding='utf-8-sig',newline='') as stream:result.to_csv(stream,index=False)

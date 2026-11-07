"""Deterministic paid-FA context selection; exact deduplication preserves all predeclared origin labels."""
import numpy as np
from run_long_budget_bridge import rows,write_once
from fixed_fa_build import SOURCE


def assignment(genome):
    js,fa=genome['JS'],genome['FA'];assert sorted(js)==list(range(len(js)))
    result=[None]*len(js)
    for job,factory in zip(js,fa):result[job]=factory
    return tuple(result)


def genome_key(row):return tuple(tuple(row[k]) for k in ('JS','FA','MA','WA'))


def select_contexts(root,spec):
    stem=spec['stem'];norm=spec['normalization'];contexts={}
    for origin in ('FULL','NSGA'):
        folder=SOURCE/stem/('FE-'+('FULL_NAT' if origin=='FULL' else 'NSGA_NAT'))
        choices=[r for r in rows(folder/'checkpoint-solutions.jsonl') if r['checkpointKind']=='FE' and r['checkpoint']==5100]
        assert choices and all(r['bornFE']<=r['checkpointFE']==5100 for r in choices)
        for direction in ('C','E','W','BALANCED'):
            def score(row):
                point=(np.asarray(row['objectives'])-norm['lower'])/norm['scale']
                return float(point.sum()) if direction=='BALANCED' else float(point[('C','E','W').index(direction)])
            selected=min(choices,key=lambda row:(score(row),genome_key(row)));fa=assignment(selected)
            assert set(fa)==set(range(int(stem.split('_')[2])))
            if fa not in contexts:contexts[fa]={'contextId':f'fa{len(contexts):03d}','factoryByJob':list(fa),'sources':[]}
            contexts[fa]['sources'].append({'origin':origin,'direction':direction,'bornFE':selected['bornFE'],
                'sourceFE':5100,'sourceObjectives':selected['objectives'],
                'sourceGenome':{k:selected[k] for k in ('JS','FA','MA','WA')}})
    values=list(contexts.values());folder=root/stem/'contexts';folder.mkdir()
    for context in values:(folder/(context['contextId']+'.txt')).write_text(','.join(map(str,context['factoryByJob']))+'\n',encoding='utf-8')
    write_once(root/stem/'contexts.json',values);return values

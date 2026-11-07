"""Post-hoc description of already evaluated offspring; cannot alter the frozen gate or select a new method."""
from collections import Counter, defaultdict
from pathlib import Path
import sys
import numpy as np
from run_long_budget_bridge import read, rows, write_once
from research.composition_oracle.volume import UncoveredVolume
from mating_pool_analysis import METHODS


def key(point):
    return tuple(tuple(point[k]) for k in ('JS','FA','MA','WA','objectives'))


def job_resources(point):
    return {job:tuple(point[k][p] for k in ('FA','MA','WA')) for p,job in enumerate(point['JS'])}


def describe(root,spec):
    stem,norm=spec['stem'],spec['normalization'];raw=rows(root/stem/'probe/outcomes.jsonl')
    parent_gains={m:[] for m in METHODS};groups=defaultdict(lambda:defaultdict(float));paired={}
    for context in read(root/stem/'contexts.json'):
        normalize=lambda values:(np.asarray(values).reshape(-1,3)-norm['lower'])/norm['scale']
        scorer=UncoveredVolume(normalize(context['background']),(1.5,)*3)
        own=[r for r in raw if r['context']==context['contextId']]
        gains=scorer.gains(normalize([r['objectives'] for r in own]))
        accumulated=defaultdict(float)
        for r,gain in zip(own,gains):
            parent=context['current'][r['currentRecipientIndex']];child=r['child']
            a,b=job_resources(parent),job_resources(child)
            d=groups[(r['method'],r['donorRole'])];d['offspring']+=1;d['positiveOffspring']+=int(gain>1e-12)
            d['summedSingleAddedHV']+=float(gain);d['repairEdits']+=r['repairEdits']
            d['meanJSChangedFraction']+=sum(x!=y for x,y in zip(parent['JS'],child['JS']))/len(a)
            d['meanJobTupleChangedFraction']+=sum(a[j]!=b[j] for j in a)/len(a)
            accumulated[(r['method'],r['recipient'])]+=float(gain)/16
            pair=(context['contextId'],r['recipient'],r['rep'])
            paired.setdefault(pair,[]).append((r['method'],r['constructionNoise'],key(child)))
        for (method,recipient),gain in accumulated.items():parent_gains[method].append(gain)
    role_summary=[]
    for (method,role),d in sorted(groups.items()):
        n=d['offspring'];total=sum(v['summedSingleAddedHV'] for (m,_),v in groups.items() if m==method)
        role_summary.append({'method':method,'donorRole':role,'offspring':int(n),'positiveOffspring':int(d['positiveOffspring']),
            'summedSingleAddedHV':d['summedSingleAddedHV'],'shareOfMethodSingleAddedHV':d['summedSingleAddedHV']/total if total else None,
            'meanRepairEdits':d['repairEdits']/n,'meanJSChangedFraction':d['meanJSChangedFraction']/n,
            'meanJobTupleChangedFraction':d['meanJobTupleChangedFraction']/n})
    concentration={}
    for method,values in parent_gains.items():
        assert len(values)==48
        ordered=sorted(values,reverse=True);total=sum(values)
        concentration[method]={'positiveParents':sum(v>1e-12 for v in values),'top1Share':ordered[0]/total if total else None,
            'top5Share':sum(ordered[:5])/total if total else None}
    identical=0
    for entries in paired.values():
        assert len(entries)==4 and {m for m,_,_ in entries}==set(METHODS) and len({n for _,n,_ in entries})==1
        identical+=int(len({k for _,_,k in entries})==1)
    return {'stem':stem,'roleSummary':role_summary,'concentration':concentration,'pairedConstructionCases':len(paired),
        'allFourArmsIdenticalChildren':identical,'additionalSearchFE':0,'additionalDecodes':0,
        'limits':'Descriptive post-hoc only. Selected role, recipient, context and genotype are confounded; no causal role credit, '
                 'new selector, promotion of RANDOM_SHARED or change to original gate. Single-child gains are not joint batch HV.'}


def main():
    root=Path(sys.argv[1]).resolve();destination=root/'posthoc-descriptive';destination.mkdir()
    import shutil
    shutil.copy2(__file__,destination/'mating_pool_attribution.py')
    specs=read(root/'protocol.json')['instances']
    result={'instances':[describe(root,s) for s in specs],'frozenGateUnchanged':True}
    write_once(destination/'attribution.json',result)
    for r in result['instances']:
        print(r['stem'],'identical',r['allFourArmsIdenticalChildren'],'of',r['pairedConstructionCases'])
        for row in r['roleSummary']:
            if row['method'] in ('SHARED','RANDOM_SHARED'):
                print(row['method'],row['donorRole'],'n',row['offspring'],'positive',row['positiveOffspring'],
                      'HVshare',row['shareOfMethodSingleAddedHV'],'tupleChange',row['meanJobTupleChangedFraction'])


if __name__=='__main__':main()

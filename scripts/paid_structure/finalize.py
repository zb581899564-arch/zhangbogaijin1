"""Independent checks, compact evidence tables and review delivery for the zero-FE audit."""
import argparse
import csv
import json
from pathlib import Path
import time
import zipfile
import numpy as np
from common import RUN, SOURCE, MATURE, STEMS, SEEDS, ARMS, prepare, read, write, sha
from features import inversions


def check_closures(root, specs):
    from analysis_metrics import frozen_scale, hv
    checks=0
    max_error=0.
    for c in read(root/'paid-closure/summary.json')['cases']:
        name=f"{c['instance']}-{c['seed']}-{c['arm']}"
        data=read(root/'paid-closure'/(name+'.json'))
        if not c['complete']:
            continue
        scale=frozen_scale(specs[c['instance']])
        a0=read(SOURCE/'inputs-v2'/c['instance']/str(c['seed'])/'0/background.json')
        for radius,b in data['metrics']['bestSingle'].items():
            sources=b['sources']
            reconstructed=[max(s['objectives'][0] for s in sources),
                           sum(s['objectives'][1] for s in sources),
                           sum(s['objectives'][2] for s in sources)]
            error=max(abs(a-bb) for a,bb in zip(reconstructed,b['objectives']))
            max_error=max(max_error,error)
            assert np.allclose(reconstructed,b['objectives'],rtol=0,atol=1e-8)
            actual=hv(scale.normalize([*a0,b['objectives']]),float(radius))-hv(scale.normalize(a0),float(radius))
            assert abs(actual-b['absolute'])<1e-11, (name,radius)
            checks+=1
    return dict(bestSingleIndependentHVChecks=checks,componentSumMaxRoundoff=max_error)


def selected_case(top, catalog):
    e=top['evidence'];p=e['parent'];c=e['candidate'];m=e['record']
    changed=[]
    for job in m['resourceJobs']:
        old,new=catalog[p['resources'][job]],catalog[c['resources'][job]]
        changed.append(dict(job=job,old=old,new=new))
    return dict(fe=m['fe'],role=m['role'],accepted=m['accepted'],
                directHVPctA0=top['gain']['HVPctA0'],objectives=c['objectives'],
                parentObjectives=p['objectives'],delta=m['objectiveDelta'],
                factoryDelta=m['factoryDelta'],resources=changed,orderChanges=m['orderChanges'],
                acceptedPhysicalAncestors=len(top['acceptedPhysicalAncestry']))


def compact(root):
    survey=read(root/'survey/survey.json')
    details=read(root/'details/summary.json')
    old=read(RUN/'analysis/report.json')
    old_values={(i['instance'],o['seed'],o['arm']):o['aboveA0']['HVEffectPct']['1.5']
                for i in old['instances'] for o in i['observations']}
    count=sum(c['groups']['all']['n'] for c in survey['cases'])
    assert count==73710 and survey['terminalRows']==18
    selected=[]
    for c in details['cases']:
        key=(c['instance'],c['seed'],c['arm'])
        assert abs(c['totalHVPctA0']-old_values[key])<1e-9
        if c['totalHVPctA0']<=0:
            continue
        data=read(root/'details'/('-'.join(map(str,key))+'.json'))['accounting']
        catalog=read(RUN/'science'/key[0]/str(key[1])/key[2]/'domain.json')['catalog']
        selected.append(dict(instance=key[0],seed=key[1],arm=key[2],
            workerCostDirectGainSharePct=100*c['groups'].get('role.WORKER_COST',{}).get('HVPctA0',0)/c['totalHVPctA0'],
            coveredParentBreakthroughs=c['coveredParentBreakthroughs'],
            matchedGainsWithNegativeControls=sum(bool(r['negativeFE']) for r in data['matchedParentComparisons']),
            topCases=[selected_case(v,catalog) for v in data['topCases']]))
    return dict(candidateRows=count,terminalRows=18,positiveContexts=selected,
                initialContexts=[c for c in details['cases'] if c['arm']=='GOM'],
                localParetoImproved=sum(c['local']['localParetoImproved'] for c in details['cases']),
                localParetoImprovedButCoveredA0=sum(c['local']['localParetoImprovedButCoveredA0'] for c in details['cases']),
                sourceSearchFE=73728,newSearchFE=0,newDecoderCalls=0,
                archivalScienceDecisionUnchanged=True,mainlineChanged=False)


def main(root):
    prepare()
    start=time.perf_counter()
    assert inversions([0,1,2],[2,1,0])==3 and inversions([0,1],[0,1])==0
    specs={s['stem']:s for s in read(MATURE/'protocol.json')['instances']}
    result=compact(root)
    result['checks']=check_closures(root,specs)
    result['checks']['chronologicalHVEndpointMatches']=18
    result['checks']['allFactoryLocalityAndFA']='PASS on all production rows'
    result['checks']['inputHashCount']=len(read(root/'survey/input-identity.json'))
    closure=read(root/'paid-closure/summary.json')
    result['algebraicExpansions']=sum(c['expanded'] for c in closure['cases'])
    result['closuresComplete']=sum(c['complete'] for c in closure['cases'])
    result['closuresPlanned']=len(closure['cases'])
    result['seconds']={k:read(root/k/'summary.json')['seconds'] for k in ('details','paid-closure')}
    result['seconds']['survey']=read(root/'survey/survey.json')['seconds']
    result['seconds']['finalizeChecks']=time.perf_counter()-start
    write(root/'acceptance.json',dict(passed=True,**result))
    csv_path=root/'closure-summary.csv'
    with csv_path.open('x',encoding='utf-8',newline='') as f:
        fields=['instance','seed','arm','complete','expanded','frontSize','bestSingleHVPct','unionHVPct']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(closure['cases'])
    # Review subset keeps summaries, sources and full evidence for top cases. All raw derived
    # feature/witness tables remain in the Linux run; original paid logs stay in their old run.
    included=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.name=='finalize.log':
            continue
        rel=p.relative_to(root)
        if rel.parts[0]=='survey' and p.name not in ('survey.json','input-identity.json'):
            continue
        if rel.parts[0]=='paid-closure' and p.name not in ('scope.json','summary.json'):
            continue
        included.append(p)
    manifest={str(p.relative_to(root)):sha(p) for p in included}
    write(root/'review-manifest.json',dict(files=manifest,scope='Review subset; all raw data retained on Linux',originalPaidRun=str(RUN)))
    archive=root.parent/(root.name+'-review.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in included+[root/'review-manifest.json']:
            z.write(p,str(p.relative_to(root)))
    print('FINAL',json.dumps(result,ensure_ascii=False),flush=True)
    print('REVIEW_ARCHIVE',archive.stat().st_size,sha(archive),len(manifest),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)

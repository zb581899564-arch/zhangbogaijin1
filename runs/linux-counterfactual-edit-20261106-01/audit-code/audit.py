"""Audit actual class identities, frozen atom matrices and paid physical timelines."""
import argparse
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse,unquote
import zipfile
import numpy as np
from cf_common import *


def loaded_identity(root,receipt):
    identity=read(root/'build-01/identity.json')
    old=read(OLD/'science/20_8_5_1/16110003/LEGAL/receipt.json')['loaded']
    checks=0
    for name,meta in receipt['loaded'].items():
        if not isinstance(meta,dict):continue
        resource=meta['resource']
        if resource.startswith('file:'):
            path=Path(unquote(urlparse(resource).path));digest=sha(path)
            newclasses=root/'build-01/classes'
            if path.is_relative_to(newclasses):
                expected=identity['classes'][str(path.relative_to(newclasses))]
            else:
                expected=None
                for base,entries in identity['dependencies'].items():
                    if isinstance(entries,dict) and path.is_relative_to(Path(base)):
                        expected=entries[str(path.relative_to(Path(base)))];break
                assert expected is not None,path
            assert digest==meta['sha256']==expected
        else:
            raise AssertionError('Unexpected class resource; investigate instead of bypassing: '+resource)
        if name in old:assert meta['sha256']==old[name]['sha256']
        checks+=1
    return checks


def timeline(row):
    steps=row['steps'];jobs=len(row['JS']);seen=set();resources=defaultdict(list);by_operation={}
    by_job={j:(f,m,w) for j,f,m,w in zip(*(row[k] for k in FIELDS))}
    per_factory=defaultdict(list)
    for s in steps:
        j,f,k,m,w=s[:5];start,base,duration,setup,end,u,v,energy,labor,exposure=s[5:]
        assert (j,k) not in seen;seen.add((j,k));assert by_job[j][0]==f
        if k==0:assert by_job[j][1:]==(m,w)
        assert start>=0 and duration>0 and end==start+duration
        assert all(np.isfinite(s))
        resources['machine',f,k,m].append((start,end))
        resources['worker',f,k,w].append((start,end))
        per_factory[f].append(s);by_operation[j,k]=s
    stages=max(s[2] for s in steps)+1
    assert len(seen)==jobs*stages
    assert row['recomputedOperations']==len(steps) and row['reusedOperations']==0
    for j in range(jobs):
        for k in range(1,stages):assert by_operation[j,k-1][9]<=by_operation[j,k][5]+1e-8
    for values in resources.values():
        values.sort()
        assert all(a[1]<=b[0]+1e-8 for a,b in zip(values,values[1:]))
    maxerr=0.
    for f,values in per_factory.items():
        # DynamicStep.energy already contains the preceding machine idle charge.
        actual=[max(s[9] for s in values),sum(s[12] for s in values),sum(s[13] for s in values)]
        expected=[row[k][f] for k in ('factoryMakespan','factoryEnergy','factoryCost')]
        error=max(abs(a-b) for a,b in zip(actual,expected));maxerr=max(maxerr,error)
        assert error<2e-8,(row['id'],row['mask'],f,error)
    aggregate=[max(row['factoryMakespan']),sum(row['factoryEnergy']),sum(row['factoryCost'])]
    assert np.allclose(aggregate,row['objectives'],rtol=0,atol=2e-8)
    return len(steps),maxerr


def matrix_entry(case,row):
    mask=row['mask'];p,c=case['parent'],case['child'];a,b=case['jobs']
    # Independently assign each component by mask instead of trusting exported vectors.
    for j in range(len(p['resources'])):
        bit=1 if j==a else 2 if j==b else 0
        expected_resource=c['resources'][j] if bit and mask&bit else p['resources'][j]
        expected_key=c['keys'][j] if bit and mask&(bit<<2) else p['keys'][j]
        assert row['resources'][j]==expected_resource and row['keys'][j]==expected_key
    for field,values in encode(row['resources'],row['keys'],case['catalog']).items():assert row[field]==values
    assert dict(zip(row['JS'],row['FA']))==dict(zip(p['JS'],p['FA']))
    if mask in (0,15):assert row['objectives']==(p if mask==0 else c)['objectives']
    return timeline(row)


def run(root,phase):
    prepare();protocol=read(root/'protocol.json')
    assert protocol['plannedNewEvaluations']==14*protocol['pairs']<=364
    assert protocol['plannedQA']==2*protocol['pairs']<=52
    cases={c['id']:read(root/'cases'/(c['id']+'.json')) for c in protocol['cases']}
    source_checks=0
    for name,digest in read(root/'input-identity.json').items():
        assert sha(name)==digest;source_checks+=1
    counts=defaultdict(set);evaluated=0;operations=0;classes=0;maxerror=0.
    categories=('qa',) if phase=='qa' else ('qa','paid')
    for kind in categories:
        assert read(root/(kind+'-complete.json'))['passed']
        for stem in STEMS:
            folder=root/kind/stem
            if not folder.exists():continue
            receipt=read(folder/'receipt.json');classes+=loaded_identity(root,receipt)
            results=lines(folder/'evaluations.jsonl')
            for number,row in enumerate(results,1):
                assert row['number']==number
                assert row['mask'] not in counts[row['id']]
                count,error=matrix_entry(cases[row['id']],row)
                counts[row['id']].add(row['mask']);operations+=count;maxerror=max(maxerror,error);evaluated+=1
    expected={0,15} if phase=='qa' else set(range(16))
    assert set(counts)==set(cases) and all(v==expected for v in counts.values())
    report=dict(passed=True,phase=phase,cases=len(cases),rows=evaluated,operationRecords=operations,
                classChecks=classes,sourceIdentityChecks=source_checks,maxIndependentAggregationError=maxerror,
                newDecoderCallsByAudit=0,allFrozenAtoms=True,fixedFA=True,unchangedMainline=True)
    write(root/(phase+'-independent-audit.json'),report);print('AUDIT_PASS',report,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--phase',choices=['qa','paid'],required=True);args=p.parse_args();run(args.root,args.phase)

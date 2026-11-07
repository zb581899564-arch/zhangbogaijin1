"""Independent matching, immutable identity and physical-timeline checks."""
import argparse
import importlib.util
from collections import Counter
from urllib.parse import urlparse,unquote
from common import *


def verify_prepared(root):
    gate=read(root/'opportunity-gate.json')
    for path,digest in gate['preparedHashes'].items():assert sha(root/path)==digest
    entries,models,catalog=load_sources();entries={e['id']:e for e in entries}
    queries={r['id']:r for r in stream(root/'prepared/queries.jsonl')}
    trees={t['context']:t for t in read(root/'prepared/trees.json')}
    counts=Counter();checked=0
    for e in entries.values():
        t=trees[e['id']];m=models[str(e['cycle'])];perm=t['permutation']
        assert sorted(perm)==list(range(100))
        assert t['trees']['POST_FA']==m['nativeFOS'] and t['trees']['PRE_FA_STATS']==m['hybridFOS']
        assert t['trees']['RANDOM_FOS']==[sorted(perm[j] for j in mask) for mask in m['hybridFOS']]
    for s in stream(root/'prepared/schedule.jsonl'):
        entry=entries[s['context']];free=[p for p in entry['S'] if p['family']==-1]
        parent,donor=free[s['receiverFreeIndex']],free[s['donorFreeIndex']]
        assert parent['slot']==s['receiver'] and donor['slot']==s['donor'] and parent['slot']!=donor['slot']
        for arm in ARMS:
            q=queries[s['id']+'-'+arm];mask=trees[s['context']]['trees'][arm][s['node']]
            assert q['fos']==mask and 100<=s['node']<198
            resources=[donor['resources'][j] if j in mask else parent['resources'][j] for j in range(100)]
            keys=[donor['keys'][j] if j in mask else parent['keys'][j] for j in range(100)]
            fallback=len({catalog[r][0] for r in resources})!=max(t[0] for t in catalog)+1
            if fallback:resources,keys=parent['resources'],parent['keys']
            assert (q['resources'],q['keys'],q['fallback'])==(resources,keys,fallback)
            assert all(q[k]==v for k,v in encode(resources,keys,catalog).items())
            counts[s['context'],arm,s['role']]+=1;checked+=1
    assert checked==1152 and all(v==32 for v in counts.values()) and len(counts)==36
    write(root/'prepared-audit.json',dict(passed=True,queries=checked,roleCells=len(counts),
          randomizedTreeIsExactRelabeling=True,allReceiverDonorAndKeyAssignmentsChecked=True,newFE=0,newQA=0))


def loaded(identities):
    frozen=read(SUPPORT/'build/identity.json');checks=0
    for name,meta in identities.items():
        if not isinstance(meta,dict):continue
        assert meta['resource'].startswith('file:')
        path=Path(unquote(urlparse(meta['resource']).path));expected=None
        classes=SUPPORT/'build/classes'
        if path.is_relative_to(classes):expected=frozen['classes'][str(path.relative_to(classes))]
        else:
            for base,values in frozen['dependencies'].items():
                if isinstance(values,dict) and path.is_relative_to(Path(base)):
                    expected=values[str(path.relative_to(Path(base)))];break
        assert expected is not None and sha(path)==meta['sha256']==expected,name
        checks+=1
    return checks


def timelines(root):
    assert read(root/'accounting.json')['passed']
    legacy=BASE/'runs/linux-counterfactual-edit-20261106-01/audit-code/audit.py'
    sys.path.insert(0,str(legacy.parent))
    module_spec=importlib.util.spec_from_file_location('frozen_timeline_audit',legacy)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    classes=operations=total=0;maximum=0.;physical_values={}
    for kind in ('qa','paid'):
        expected={r['id']:r for r in stream(root/'prepared'/('qa.jsonl' if kind=='qa' else 'queries.jsonl'))}
        seen=set()
        for folder in sorted((root/kind).iterdir()):
            classes+=loaded(read(folder/'receipt.json')['loaded'])
            for number,r in enumerate(stream(folder/'evaluations.jsonl'),1):
                assert r['number']==number and r['id'] not in seen
                q=expected[r['id']];assert all(r[k]==q[k] for k in (*FIELDS,'resources','keys'))
                if kind=='qa':assert r['objectives']==q['objectives']
                count,error=module.timeline(r);operations+=count;maximum=max(maximum,error);total+=1;seen.add(r['id'])
                key=physical(r)
                if key in physical_values:assert physical_values[key]==r['objectives']
                physical_values[key]=r['objectives']
        assert seen==set(expected)
    assert total==1176
    write(root/'independent-audit.json',dict(passed=True,rows=total,actualCandidateFE=1152,actualQA=24,
          operationRecords=operations,maxIndependentAggregationError=maximum,loadedClassChecks=classes,
          uniquePhysicalSchedules=len(physical_values),newDecoderCallsByAudit=0,
          reusedTimelineCheckerSHA256=sha(legacy),sourceMatchingGate=read(root/'prepared-audit.json')))
    print('INDEPENDENT_AUDIT_PASSED',total,operations,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('phase',choices=['prepared','timelines'])
    args=p.parse_args();linux();verify_prepared(args.root) if args.phase=='prepared' else timelines(args.root)

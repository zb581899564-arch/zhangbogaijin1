"""Select only from already-paid outcomes; freeze all cases before new evaluation."""
import argparse
from pathlib import Path
import numpy as np
from cf_common import *


def trace(stem,seed,arm,identity):
    folder=OLD/'science'/stem/str(seed)/arm
    names=('before.json','paid.jsonl','steps.jsonl','domain.json')
    manifest=read(OLD/'delivery-manifest.json')
    for n in names:
        path=folder/n;digest=sha(path)
        assert digest==manifest[str(path.relative_to(OLD))]
        identity[str(path)]=digest
    before=read(folder/'before.json');live={r['slot']:r for r in before}
    background_path=REQUEST/'inputs-v2'/stem/str(seed)/'0/background.json'
    a0=read(background_path);identity[str(background_path)]=sha(background_path)
    catalog=read(folder/'domain.json')['catalog'];archive=np.asarray(a0,float)
    result=[]
    for paid,step in zip(lines(folder/'paid.jsonl'),lines(folder/'steps.jsonl')):
        assert paid['fe']==step['fe']
        parent=live[step['slot']]
        assert parent['objectives']==step['parentObjectives']
        novel=not bool(np.any(np.all(np.asarray(a0)<=paid['objectives'],axis=1)))
        changed=physical(parent)!=physical(paid)
        result.append(dict(instance=stem,seed=seed,arm=arm,fe=paid['fe'],parent=parent,
            child=paid,step=step,novelA0=novel,changed=changed,catalog=catalog))
        if step['accepted']:live[step['slot']]=paid
    assert len(result)==4095
    return result,a0


def choose(alltraces):
    selected=[];missing=[]
    for arm in ARMS:
        records=alltraces['100_2_3_1',16110037,arm][0]
        for role in ('CENTER','WORKER_COST'):
            parents=set();chosen=[]
            for r in records:
                signature=physical(r['parent'])
                if r['step']['fresh'] and r['changed'] and r['step']['role']==role and signature not in parents:
                    parents.add(signature);chosen.append(r)
                    if len(chosen)==2:break
            if len(chosen)<2:missing.append(dict(arm=arm,role=role,missingPositive=2-len(chosen)))
            for r in chosen:
                pos_id=f'case-{len(selected):02d}'
                selected.append(dict(r,id=pos_id,label='POSITIVE'))
                controls=[c for c in records if c['step']['parentId']==r['step']['parentId']
                          and c['child']['generation']['factory']==r['child']['generation']['factory']
                          and c['changed'] and not c['novelA0']]
                if controls:
                    selected.append(dict(controls[0],id=f'case-{len(selected):02d}',label='MATCHED_NEGATIVE',matchedPositive=pos_id))
                else:missing.append(dict(positive=pos_id,missingNegative=True))
    for stem in STEMS:
        for seed in SEEDS:
            if (stem,seed)==('100_2_3_1',16110037):continue
            for arm in ARMS:
                eligible=[r for r in alltraces[stem,seed,arm][0] if r['changed']]
                if not eligible:
                    missing.append(dict(instance=stem,seed=seed,arm=arm,missingBackground=True));continue
                selected.append(dict(eligible[0],id=f'case-{len(selected):02d}',label='BACKGROUND_NEGATIVE'))
    assert len(selected)<=26
    return selected,missing


def archive_before(a0,records,fe):
    a=np.asarray(a0,float)
    for r in records[:fe-1]:
        obj=np.asarray(r['child']['objectives'])
        if not np.any(np.all(a<=obj,axis=1)):
            a=np.vstack([a[~np.all(obj<=a,axis=1)],obj])
    return a.tolist()


def export(root,selected,traces):
    tsv={s:{'qa':[],'paid':[]} for s in STEMS}
    summary=[]
    for r in selected:
        stem,seed,arm=r['instance'],r['seed'],r['arm'];records,a0=traces[stem,seed,arm]
        parent,child=r['parent'],r['child'];jobs=child['generation']['jobs']
        assert len(jobs)==2 and jobs[0]!=jobs[1]
        variants=[]
        for mask in range(16):
            v=variant(parent,child,jobs,mask,r['catalog'])
            fixed=dict(zip(parent['JS'],parent['FA']))
            assert all(fixed[j]==f for j,f in zip(v['JS'],v['FA']))
            expected=parent if mask==0 else child if mask==15 else None
            if expected:
                assert all(v[k]==expected[k] for k in FIELDS)
                v['objectives']=expected['objectives']
            variants.append(dict(mask=mask,**v))
            columns=[r['id'],str(mask),','.join(map(str,v['resources'])),','.join(map(repr,v['keys']))]
            columns.extend(','.join(map(str,v[k])) for k in FIELDS)
            columns.append(','.join(map(repr,v.get('objectives',[]))))
            tsv[stem]['qa' if expected else 'paid'].append('\t'.join(columns))
        detail={k:v for k,v in r.items() if k not in ('changed','novelA0')}
        detail.update(jobs=jobs,A0=a0,beforeEvent=archive_before(a0,records,r['fe']),variants=variants)
        write(root/'cases'/(r['id']+'.json'),detail)
        summary.append({k:r[k] for k in ('id','instance','seed','arm','fe','label')}|
                       dict(role=r['step']['role'],parentId=r['step']['parentId'],jobs=jobs,
                            matchedPositive=r.get('matchedPositive')))
    for stem,groups in tsv.items():
        for kind,values in groups.items():
            path=root/'inputs'/stem/(kind+'.tsv');path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x',encoding='utf-8') as f:f.write('\n'.join(values)+'\n')
    return summary


def main(root):
    prepare();assert not (root/'protocol.json').exists()
    identities={};traces={}
    for stem in STEMS:
        for seed in SEEDS:
            for arm in ARMS:traces[stem,seed,arm]=trace(stem,seed,arm,identities)
    selected,missing=choose(traces);summary=export(root,selected,traces)
    write(root/'input-identity.json',identities)
    write(root/'protocol.json',dict(cases=summary,missing=missing,pairs=len(selected),
        plannedNewEvaluations=14*len(selected),plannedQA=2*len(selected),hardLimitFE=364,hardLimitQA=52,
        bits=['resource_a','resource_b','key_a','key_b'],controls={'PARENT':0,'RESOURCE':3,'ORDER':12,'JOB_A':5,'JOB_B':10,'FULL':15},
        queryOrder='instance in fixed order, case order, masks 1..14; all QA first',
        physics='Common frozen DynamicDecoder full path; no incremental reuse or per-candidate extra QA',
        engineering='Reuse previous complete timeline full/incremental equivalence; current QA0/15 must match old objective bits',
        objectiveCertificateAbsTol=[1e-8]*3,hvNumericalAbsTol=1e-12,
        numericRule='Exact raw weak dominance for C; meaningful strict improvement exceeds abs tolerance; no tolerance dominance',
        referenceRule='For each instance, ND union of all source A0 plus all 16 configurations from all selected cases; offline only',
        keepSearchMainline=True,runTransfer=False,claimAlgorithmPerformance=False))
    print('FROZEN_CASES',len(selected),'FE',14*len(selected),'QA',2*len(selected),'MISSING',missing,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)

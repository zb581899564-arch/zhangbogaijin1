"""Freeze matched legal proposals and evaluate opportunity before any decoding."""
import argparse
from collections import Counter
from common import *


def mix(parent,donor,mask,catalog):
    resource=parent['resources'][:];keys=parent['keys'][:]
    for job in mask:resource[job]=donor['resources'][job];keys[job]=donor['keys'][job]
    fallback=len({catalog[r][0] for r in resource})!=max(c[0] for c in catalog)+1
    if fallback:resource,keys=parent['resources'][:],parent['keys'][:]
    return dict(resources=resource,keys=keys,fallback=fallback,**encode(resource,keys,catalog))


def fixtures(row,parent,donor):
    return '\t'.join([row['id'],csv_value(parent['resources']),csv_value(parent['keys']),
         csv_value(donor['resources']),csv_value(donor['keys']),csv_value(row['fos']),
         csv_value(row['resources']),csv_value(row['keys']),str(row['fallback']).lower()])


def context(entry,model,catalog):
    free=[p for p in entry['S'] if p['family']==-1];assert len(free)==80
    selected=[p for role in ROLES for p in sorted((p for p in free if p['role']==role),key=lambda p:p['slot'])[:2]]
    assert Counter(p['role'] for p in selected)==dict.fromkeys(ROLES,2)
    permutation=list(range(100));rng(entry['fe'],-1,'job-permutation').shuffle(permutation)
    random_fos=[sorted(permutation[j] for j in mask) for mask in model['hybridFOS']]
    fos=dict(zip(ARMS,(model['nativeFOS'],model['hybridFOS'],random_fos)))
    assert all(len(a)==len(b) for a,b in zip(random_fos,model['hybridFOS']))
    queries,qa,schedule,native=[],[],[],[]
    for parent in selected:
        index=next(i for i,p in enumerate(free) if p['slot']==parent['slot'])
        eligible=[i for i in range(80) if i!=index]
        masks=rng(entry['fe'],parent['slot'],'merge-indices').sample(range(100,198),16)
        donor_rng=rng(entry['fe'],parent['slot'],'donor-indices')
        qa.append(dict(parent,id=f"{entry['fe']}-{parent['slot']}-QA"))
        for step,node in enumerate(masks):
            donor_index=donor_rng.choice(eligible);donor=free[donor_index]
            key=f"{entry['fe']}-{parent['slot']}-{step}"
            schedule.append(dict(id=key,context=entry['id'],role=parent['role'],receiver=parent['slot'],
                                 receiverFreeIndex=index,donorFreeIndex=donor_index,donor=donor['slot'],node=node))
            for arm in ARMS:
                mask=fos[arm][node];assert 1<len(mask)<100
                row=dict(mix(parent,donor,mask,catalog),id=key+'-'+arm,proposal=key,context=entry['id'],
                         arm=arm,role=parent['role'],receiver=parent['slot'],donor=donor['slot'],node=node,fos=mask)
                queries.append(row);native.append(fixtures(row,parent,donor))
    mapping={q['id']:q for q in queries};changed=Counter()
    for s in schedule:
        if physical(mapping[s['id']+'-POST_FA'])!=physical(mapping[s['id']+'-PRE_FA_STATS']):changed[s['role']]+=1
    opportunity=dict(context=entry['id'],proposals=128,changed=sum(changed.values()),byRole=dict(changed),
                     passed=sum(changed.values())>=26 and len(changed)>=2)
    return queries,qa,schedule,native,dict(context=entry['id'],permutation=permutation,trees=fos),opportunity


def main(root):
    entries,models,catalog=load_sources();prepared=root/'prepared';prepared.mkdir()
    queries,qa,schedule,native,trees,gates=[],[],[],[],[],[]
    for e in entries:
        q,a,s,n,t,g=context(e,models[str(e['cycle'])],catalog)
        queries.extend(q);qa.extend(a);schedule.extend(s);native.extend(n);trees.append(t);gates.append(g)
    assert len(queries)==1152 and len(qa)==24 and len(schedule)==384
    jsonl(prepared/'queries.jsonl',queries);jsonl(prepared/'qa.jsonl',qa);jsonl(prepared/'schedule.jsonl',schedule)
    write(prepared/'trees.json',trees)
    (prepared/'native-fixture.tsv').write_text('\n'.join(native)+'\n')
    for kind,data,limit in [('qa',qa,52),('paid',queries,364)]:
        target=prepared/kind;target.mkdir()
        for begin in range(0,len(data),limit):
            (target/f'{begin//limit:03}.tsv').write_text('\n'.join(tsv_row(r,kind=='qa') for r in data[begin:begin+limit])+'\n')
    write(root/'opportunity-gate.json',dict(passed=all(g['passed'] for g in gates),contexts=gates,newFE=0,newQA=0,
          queryConstructed=1152,triggerRule='>=26/128 physical differences, >=2 roles, all3 contexts',
          preparedHashes={str(p.relative_to(root)):sha(p) for p in prepared.rglob('*') if p.is_file()},
          protocolSHA256=sha(root/'protocol.md')))
    print('OPPORTUNITY',json.dumps(gates),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)

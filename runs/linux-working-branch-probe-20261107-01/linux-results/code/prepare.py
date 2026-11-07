"""Create explicit finite programs, request archives and zero-decoder mixing fixtures."""
import argparse
import numpy as np
from common import *


def mixed(parent,donor,mask,catalog):
    resource=parent['resources'][:];keys=parent['keys'][:]
    for j in mask:resource[j]=donor['resources'][j];keys[j]=donor['keys'][j]
    fallback=len({catalog[r][0] for r in resource})!=max(t[0] for t in catalog)+1
    if fallback:resource,keys=parent['resources'][:],parent['keys'][:]
    return resource,keys,fallback


def main(root):
    cases,entries,models,catalog=sources();out=root/'prepared';out.mkdir()
    previous={r['id']:r for f in (FA/'paid').glob('*/evaluations.jsonl') for r in stream(f)}
    proposals={q['id']:q for q in stream(FA/'prepared/queries.jsonl')}
    seeds=[];case_lines=[];donor_lines=[];archive_lines=[];archives={};schedules=[];fixture=[]
    for context,e in entries.items():
        prior=[r['objectives'] for key,r in previous.items() if proposals[key]['context']==context]
        base=nd(e['S_archive']+prior+[c[tag]['objectives'] for c in cases if c['context']==context for tag in ('P','Q','R')])
        archives[context]=base.tolist()
        archive_lines.extend(context+'\t'+csv_value(p) for p in base)
        for p in e['S']:
            if p['family']==-1:donor_lines.append('\t'.join([context,str(p['slot']),csv_value(p['resources']),csv_value(p['keys'])]))
    for c in cases:
        case=c['context']+'-'+c['role'];c['id']=case
        assert proposals[c['chosenId']]['arm']=='POST_FA'
        assert all(c['Q'][k]==previous[c['chosenId']][k] for k in (*FIELDS,'resources','keys','objectives'))
        case_lines.append('\t'.join([case,c['context'],c['role'],str(c['parentSlot'])]))
        free={p['slot']:p for p in entries[c['context']]['S'] if p['family']==-1};eligible=[i for i in free if i!=c['parentSlot']]
        assert len(eligible)==79
        for tag in ('P','Q','R'):
            seed=dict(c[tag],id=case+'-'+tag);seeds.append(seed)
            assert any(all(a<=b for a,b in zip(p,seed['objectives'])) for p in archives[c['context']])
            assert all(seed[k]==v for k,v in encode(seed['resources'],seed['keys'],catalog).items())
        for branch,length in ((0,31),(1,15)):
            order=list(range(199));rng(case,branch,'fos-order').shuffle(order)
            draw=rng(case,branch,'donor-indices')
            for step,node in enumerate(order[:length]):
                donor_slot=draw.choice(eligible);donor=free[donor_slot];mask=models[c['context']]['subsets'][node]
                s=dict(case=case,context=c['context'],branch=branch,step=step,node=node,donorSlot=donor_slot,mask=mask)
                schedules.append(s)
                for tag in ('P','Q','R'):
                    parent=c[tag];resource,keys,fallback=mixed(parent,donor,mask,catalog)
                    fixture.append('\t'.join([f'{case}-{branch}-{step}-{tag}',csv_value(parent['resources']),csv_value(parent['keys']),
                        csv_value(donor['resources']),csv_value(donor['keys']),csv_value(mask),csv_value(resource),csv_value(keys),str(fallback).lower()]))
    assert len(seeds)==36 and len(schedules)==552 and len(fixture)==1656
    write(out/'cases.json',cases);write(out/'archives.json',archives);jsonl(out/'schedule.jsonl',schedules);jsonl(out/'seeds.jsonl',seeds)
    outputs={'seeds.tsv':[tsv_row(s,True) for s in seeds],'cases.tsv':case_lines,'donors.tsv':donor_lines,'archives.tsv':archive_lines,
             'native-fixture.tsv':fixture,'schedule.tsv':['\t'.join([s['case'],str(s['branch']),str(s['step']),str(s['node']),str(s['donorSlot']),csv_value(s['mask'])]) for s in schedules]}
    for name,values in outputs.items():(out/name).write_text('\n'.join(values)+'\n')
    write(root/'prepared-gate.json',dict(passed=True,cases=12,seeds=36,donors=240,explicitMoves=552,
          unscoredInitialGenomeMixingFixtures=1656,sourceRerunFE=0,newFE=0,newQA=0,
          inputHashes={str(p):sha(p) for p in (CAPACITY/'cases.json',SUPPORT/'prepared/entries.json',FA/'analysis/fronts.json')},
          preparedHashes={p.name:sha(p) for p in out.glob('*') if p.is_file()},protocolSHA256=sha(root/'protocol.md')))
    print('PREPARED',12,36,552,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)

"""Existing-paid-data feasibility only; never generates or decodes a schedule."""
from pathlib import Path
import csv
import hashlib
import json
import sys

BASE=Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
SOURCE=BASE/'runs/linux-mid-support-20261107-01'
PROBE=BASE/'runs/linux-fa-stat-query-20261107-01'
ROLES=('MAKESPAN','CENTER','ENERGY','WORKER_COST')
FIELDS=('JS','FA','MA','WA','resources','keys','objectives')


def load(path):return json.loads(path.read_text())
def rows(path):return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
def weak(a,b):return all(x<=y for x,y in zip(a,b))


def eligible(parent,child,population,archive,role):
    p,v=parent['objectives'],child['objectives']
    if weak(v,p) or weak(p,v) or any(weak(s['objectives'],v) for s in population):return False
    if role=='CENTER':return any(weak(s,v) and s!=v for s in archive)
    index={'MAKESPAN':0,'ENERGY':1,'WORKER_COST':2}[role]
    return v[index]>p[index]  # Exclude previously tested objective-equal plateaus.


def main(root):
    assert sys.platform=='linux';root.mkdir(exist_ok=False)
    entries=load(SOURCE/'prepared/entries.json');queries=rows(PROBE/'prepared/queries.jsonl')
    actual={r['id']:r for f in sorted((PROBE/'paid').glob('*/evaluations.jsonl')) for r in rows(f)}
    with (PROBE/'analysis/single-candidates.csv').open(encoding='utf-8-sig') as f:
        accepted={r['id']:r['wouldAccept'] for r in csv.DictReader(f) if r['background']=='S_archive'}
    cases=[]
    for entry in entries:
        for role in ROLES:
            members=sorted((p for p in entry['S'] if p['family']==-1 and p['role']==role),key=lambda p:p['slot'])
            parent,other=members[:2];choices=[]
            for q in queries:
                if q['context']!=entry['id'] or q['arm']!='POST_FA' or q['receiver']!=parent['slot']:continue
                if eligible(parent,actual[q['id']],entry['S'],entry['S_archive'],role):
                    assert accepted[q['id']]=='False';choices.append(q)
            choices.sort(key=lambda q:int(q['proposal'].rsplit('-',1)[1]))
            chosen=choices[0] if choices else None
            cases.append(dict(context=entry['id'],role=role,parentSlot=parent['slot'],ordinaryOtherSlot=other['slot'],
                eligibleNativeBranches=len(choices),chosenId=chosen['id'] if chosen else None,
                P={k:parent[k] for k in FIELDS},R={k:other[k] for k in FIELDS},
                Q={k:actual[chosen['id']][k] for k in FIELDS} if chosen else None))
    assert len(cases)==12
    summary=dict(all12CellsAvailable=all(c['chosenId'] for c in cases),eligibleNativeCandidates=sum(c['eligibleNativeBranches'] for c in cases),
        cases=[{k:c[k] for k in ('context','role','parentSlot','ordinaryOtherSlot','eligibleNativeBranches','chosenId')} for c in cases],
        newFE=0,newQA=0,newDecoderCalls=0,newCandidates=0,
        provenance='Q is a paid POST_FA counterfactual candidate, not an event of the original natural 500k trajectory.',
        selection='first free parent/second same-role free parent; first eligible POST_FA step; no HV ranking',
        noveltyLimit='feasible input states only, no continuation or algorithm benefit established',
        inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE/'prepared/entries.json',PROBE/'prepared/queries.jsonl',PROBE/'analysis/single-candidates.csv')})
    (root/'cases.json').write_text(json.dumps(cases,indent=2));(root/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))

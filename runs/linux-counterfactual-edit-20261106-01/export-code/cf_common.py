"""Frozen paths and append-only evidence for the bounded counterfactual audit."""
import hashlib
import json
from pathlib import Path
import platform
import sys

BASE=Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
OLD=BASE/'runs/linux-fixed-fa-domain-production-20261106-01'
REQUEST=BASE/'runs/linux-request-conditioned-production-20261106-01'
ANALYSIS=BASE/'runs/linux-paid-structure-analysis-20261106-01'
MATURE=BASE/'runs/linux-mature-donor-20261106-01'
ANCHOR=BASE/'runs/linux-pilot-evaluation-20261106-01'
STEMS=('20_8_5_1','100_2_3_1')
SEEDS=(16110003,16110037,16110069)
ARMS=('LEGAL','NOVEL')
FIELDS=('JS','FA','MA','WA')


def prepare():
    assert platform.system()=='Linux', 'All scientific computation belongs on Linux'
    sys.path.extend(map(str,(ANCHOR/'payload',MATURE/'analysis-code',OLD/'analysis-code-v2')))


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def lines(path):
    with Path(path).open(encoding='utf-8-sig') as stream:return [json.loads(s) for s in stream if s.strip()]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def physical(row):
    factories=max(row['FA'])+1
    return (tuple(row['resources']),tuple(tuple(j for j,f in zip(row['JS'],row['FA']) if f==i) for i in range(factories)))


def encode(resources,keys,catalog):
    js=sorted(range(len(keys)),key=lambda j:(keys[j],-j))
    return dict(JS=js,FA=[catalog[resources[j]]['factory'] for j in js],
                MA=[catalog[resources[j]]['machine'] for j in js],
                WA=[catalog[resources[j]]['worker'] for j in js])


def variant(parent,child,jobs,mask,catalog):
    resources=list(parent['resources']);keys=list(parent['keys'])
    for i,j in enumerate(jobs):
        if mask&(1<<i):resources[j]=child['resources'][j]
        if mask&(1<<(i+2)):keys[j]=child['keys'][j]
    return dict(resources=resources,keys=keys,**encode(resources,keys,catalog))

"""Linux-only frozen sources, exact metrics and bounded-run IO."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
import time

BASE=Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
SUPPORT=BASE/'runs/linux-mid-support-20261107-01'
FA=BASE/'runs/linux-fa-stat-query-20261107-01'
CAPACITY=BASE/'runs/linux-working-branch-capacity-20261107-01'
spec=importlib.util.spec_from_file_location('support_common',SUPPORT/'source/scripts/common.py')
support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
read,rows,write,sha,stream,jsonl=support.read,support.rows,support.write,support.sha,support.stream,support.jsonl
encode,physical,csv_value,tsv_row=support.encode,support.physical,support.csv_value,support.tsv_row
nd,metrics,coverage,csv_write=support.nd,support.metrics,support.coverage,support.csv_write
execute,JAVA,ANCHOR,SCALE,FIELDS=support.execute,support.JAVA,support.ANCHOR,support.SCALE,support.FIELDS
ARMS=('ONE','RESTART','CURRENT','BRANCH')
ROLES=('MAKESPAN','CENTER','ENERGY','WORKER_COST')


def linux():assert sys.platform=='linux' and sys.version_info[:2]==(3,11)
def input_args():return support.input_args()


def rng(case,branch,purpose):
    key=f'working-branch-v1|14910003|{case}|{branch}|{purpose}'
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big'))


def java(root,entry):
    return ['nice','-n','10',str(JAVA),'-Xms128m','-Xmx2g','-cp',
            (root/'build-02/classpath.txt').read_text().strip(),entry]


def frozen(path,owner):
    manifest=read(owner/'delivery-manifest.json');assert sha(path)==manifest[str(path.relative_to(owner))]['sha256']


def sources():
    frozen(CAPACITY/'cases.json',CAPACITY);frozen(SUPPORT/'prepared/entries.json',SUPPORT)
    frozen(SUPPORT/'sources/models.json',SUPPORT);frozen(FA/'analysis/fronts.json',FA)
    cases=read(CAPACITY/'cases.json');entries={e['id']:e for e in read(SUPPORT/'prepared/entries.json')}
    assert len(cases)==12 and all(c['chosenId'] for c in cases)
    models={m['context']:m for m in read(SUPPORT/'sources/models.json')['models']}
    return cases,entries,models,read(SUPPORT/'sources/models.json')['catalog']

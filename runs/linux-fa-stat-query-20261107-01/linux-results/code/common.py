"""Frozen source adapters for the bounded FA-statistical-source query."""
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
HISTORY=BASE/'runs/linux-mid-history-20261107-01'
spec=importlib.util.spec_from_file_location('frozen_support_common',SUPPORT/'source/scripts/common.py')
support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
read,rows,write,sha= support.read,support.rows,support.write,support.sha
stream,jsonl,execute=support.stream,support.jsonl,support.execute
encode,physical,csv_value,tsv_row=support.encode,support.physical,support.csv_value,support.tsv_row
nd,metrics,coverage,csv_write=support.nd,support.metrics,support.coverage,support.csv_write
SCALE,JAVA,ANCHOR,FIELDS=support.SCALE,support.JAVA,support.ANCHOR,support.FIELDS
ARMS=('POST_FA','PRE_FA_STATS','RANDOM_FOS')
ROLES=('MAKESPAN','CENTER','ENERGY','WORKER_COST')
TIMES=(104540,179120,228840)


def linux():
    assert sys.platform=='linux' and sys.version_info[:2]==(3,11)


def rng(context,slot,purpose):
    label=f'fa-stat-query-v1|14910003|{context}|{slot}|{purpose}'
    return random.Random(int.from_bytes(hashlib.sha256(label.encode()).digest()[:8],'big'))


def java(root,entry):
    return ['nice','-n','10',str(JAVA),'-Xms128m','-Xmx2g','-cp',
            (root/'build/classpath.txt').read_text().strip(),entry]


def input_args():
    return support.input_args()


def load_sources():
    assert read(HISTORY/'independent-audit.json')['passed']
    assert read(HISTORY/'model-probe/summary.json')['passed']
    assert read(SUPPORT/'independent-audit.json')['passed']
    entries=read(SUPPORT/'prepared/entries.json')
    assert tuple(e['fe'] for e in entries)==TIMES
    models={m['context']:m for m in read(HISTORY/'model-probe/raw.json')['contexts']}
    originals={m['context']:m for m in read(SUPPORT/'sources/models.json')['models']}
    for e in entries:
        m=models[str(e['cycle'])];original=originals[e['id']]
        assert m['nativeMatrix']==original['dependency'] and m['nativeFOS']==original['subsets']
        assert len(m['nativeFOS'])==len(m['hybridFOS'])==199
    return entries,models,read(SUPPORT/'sources/models.json')['catalog']

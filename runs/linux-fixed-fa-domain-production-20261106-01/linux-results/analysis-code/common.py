"""Linux-only paths and append-only evidence utilities for domain expansion probes."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

BASE=Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
SOURCE=BASE/'runs/linux-request-conditioned-production-20261106-01'
MATURE=BASE/'runs/linux-mature-donor-20261106-01'
ANCHOR=BASE/'runs/linux-pilot-evaluation-20261106-01'
CLOSURE=BASE/'runs/linux-family-support-closure-20261106-01'
STEMS=['20_8_5_1','100_2_3_1']
SEEDS=[16110003,16110037,16110069]
ARMS=['GOM','LEGAL','NOVEL']
JAVA=BASE/'runtime/jdk17/bin/java'
PRODUCTION=4095


def linux():assert platform.system()=='Linux','Scientific computation is Linux-only'


def read(path):return json.loads(Path(path).read_text('utf-8-sig'))


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as s:json.dump(value,s,ensure_ascii=False,indent=2)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as s:
        for b in iter(lambda:s.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def lines(path):
    with Path(path).open(encoding='utf-8-sig') as s:return [json.loads(x) for x in s if x.strip()]


def execute(command,out,expected=0):
    out.mkdir(parents=True,exist_ok=False);write(out/'command.json',list(map(str,command)))
    start=time.perf_counter()
    with (out/'run.log').open('x') as s:p=subprocess.run(list(map(str,command)),stdout=s,stderr=subprocess.STDOUT)
    write(out/'process.json',dict(exitCode=p.returncode,seconds=time.perf_counter()-start))
    assert p.returncode==expected,f'Failed run retained: {out}'


"""Shared paths and append-only evidence I/O for the finite support diagnostic."""
import hashlib
import json
from pathlib import Path
import platform

BASE=Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
SOURCE=BASE/'runs/linux-request-conditioned-production-20261106-01'
SEEDS=[16110003,16110037,16110069]
STEMS=['20_8_5_1','100_2_3_1']


def linux():
    assert platform.system()=='Linux', 'Scientific work must run on Linux'


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def lines(path):
    with Path(path).open() as stream:
        yield from (json.loads(line) for line in stream if line.strip())

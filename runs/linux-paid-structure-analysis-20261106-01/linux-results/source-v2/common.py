"""Read-only provenance and Linux paths for analysis of already-paid schedules."""
import hashlib
import json
from pathlib import Path
import platform
import sys

BASE = Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
RUN = BASE / 'runs/linux-fixed-fa-domain-production-20261106-01'
SOURCE = BASE / 'runs/linux-request-conditioned-production-20261106-01'
MATURE = BASE / 'runs/linux-mature-donor-20261106-01'
ANCHOR = BASE / 'runs/linux-pilot-evaluation-20261106-01'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (16110003, 16110037, 16110069)
ARMS = ('GOM', 'LEGAL', 'NOVEL')
FACTORY = ('factoryMakespan', 'factoryEnergy', 'factoryCost')


def prepare():
    assert platform.system() == 'Linux', 'All scientific analysis executes on Linux'
    for path in (MATURE / 'analysis-code', ANCHOR / 'payload', RUN / 'analysis-code-v2'):
        sys.path.append(str(path))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, obj):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)


def rows(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def identity(paths):
    frozen = read(RUN / 'delivery-manifest.json')
    result = {}
    for path in paths:
        digest = sha(path)
        if path.is_relative_to(RUN):
            assert frozen[str(path.relative_to(RUN))] == digest, path
        result[str(path)] = digest
    return result

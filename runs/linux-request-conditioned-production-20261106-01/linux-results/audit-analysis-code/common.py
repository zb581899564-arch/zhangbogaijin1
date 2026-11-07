"""Small, append-only utilities for the Linux request-production experiment."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

BASE = Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
SOURCE = BASE / 'runs/linux-mature-donor-20261106-01'
ANCHOR = BASE / 'runs/linux-pilot-evaluation-20261106-01'
JAVA = BASE / 'runtime/jdk17/bin/java'
JAVAC = BASE / 'runtime/jdk17/bin/javac'
STEMS = ['20_8_5_1', '100_2_3_1']
SEEDS = [16110003, 16110037, 16110069]


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def linux():
    assert platform.system() == 'Linux', 'All scientific execution is Linux-only'


def process(command, out, expected=0):
    linux()
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'command.json', list(map(str, command)))
    start = time.perf_counter()
    with (out / 'run.log').open('w') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    write(out / 'process.json', dict(exitCode=result.returncode,
          seconds=time.perf_counter() - start))
    assert result.returncode == expected, f'Preserved failed run: {out}'


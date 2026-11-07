"""Shared Linux-only evidence IO and frozen-scale descriptive indicators."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np
import moocore

BASE = Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
ANCHOR = BASE / 'runs/linux-pilot-evaluation-20261106-01/payload'
ARMS = ('SHARE_CTX_GOM', 'NSGA_CTX_GOM', 'PA_JOINT')
SCALES = {'20_8_5_1': [1043.2162866718015, 51501.80947978115, 51219.63655822692],
          '100_2_3_1': [3338.756452430862, 96917.87950306736, 76604.02464302634]}


def linux():
    assert sys.platform == 'linux' and sys.version_info[:2] == (3, 11)


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def rows(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def csv_write(path, records):
    with Path(path).open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def nondominated(points):
    a = np.unique(np.asarray(points, dtype=float).reshape(-1, 3), axis=0)
    return a[moocore.is_nondominated(a)] if len(a) else a


def metrics(points, reference, scale):
    a = nondominated(points) / scale
    r = np.asarray(reference) / scale
    if not len(a):
        return {'n': 0, 'HV': 0., 'IGDplus': None, 'IGD': None}
    distances, plus = [], []
    for block in np.array_split(r, max(1, (len(r) + 127) // 128)):
        d = a[None, :, :] - block[:, None, :]
        distances.extend(np.linalg.norm(d, axis=2).min(axis=1))
        plus.extend(np.linalg.norm(np.maximum(d, 0), axis=2).min(axis=1))
    return {'n': len(a), 'HV': float(moocore.hypervolume(a, ref=[1.5]*3)),
            'IGDplus': float(np.mean(plus)), 'IGD': float(np.mean(distances))}


def coverage(a, b):
    a, b = nondominated(a), nondominated(b)
    count = sum(bool(np.any(np.all(a <= point, axis=1))) for point in b)
    return {'covered': count, 'denominator': len(b), 'C': count / len(b) if len(b) else None}


def checkpoints(folder):
    return {int(p['checkpoint']): p['front'] for p in rows(folder / 'anytime.jsonl')
            if p['checkpointKind'] == 'FE' and p.get('reached')}


def initial(folder):
    return [{k: p[k] for k in ('JS', 'FA', 'MA', 'WA', 'objectives')}
            for p in rows(folder / 'initial-population.jsonl')]

"""Paths and immutable IO for a finite, same-FA transfer diagnostic."""
import hashlib
import json
from pathlib import Path
import platform
import sys

BASE = Path('/home/inspur/codex-workspace/projects/limingzhegaijin')
CF = BASE / 'runs/linux-counterfactual-edit-20261106-01'
OLD = BASE / 'runs/linux-fixed-fa-domain-production-20261106-01'
MATURE = BASE / 'runs/linux-mature-donor-20261106-01'
ANCHOR = BASE / 'runs/linux-pilot-evaluation-20261106-01'
STEM = '100_2_3_1'
SEED = 16110037
SOURCE_MASKS = {'case-02': 6, 'case-06': 11, 'case-10': 3}
ARMS = ('FULL', 'PRUNED', 'RANDOM_0', 'RANDOM_1', 'RANDOM_2')
FIELDS = ('JS', 'FA', 'MA', 'WA')


def prepare():
    assert platform.system() == 'Linux', 'Scientific work must run on Linux'
    sys.path.extend(map(str, (CF / 'analysis-code', CF / 'audit-code',
        ANCHOR / 'payload', MATURE / 'analysis-code', OLD / 'analysis-code-v2')))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def lines(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8-sig').splitlines() if s.strip()]


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fa_map(point):
    return tuple(f for _, f in sorted(zip(point['JS'], point['FA'])))


def physical(point):
    by_factory = tuple(tuple(j for j, f in zip(point['JS'], point['FA']) if f == factory)
                       for factory in range(max(point['FA']) + 1))
    return tuple(point['resources']), by_factory


def encode(resources, keys, catalog):
    js = sorted(range(len(keys)), key=lambda j: (keys[j], -j))
    return dict(resources=resources, keys=keys, JS=js,
                FA=[catalog[resources[j]]['factory'] for j in js],
                MA=[catalog[resources[j]]['machine'] for j in js],
                WA=[catalog[resources[j]]['worker'] for j in js])


def tsv_row(point, qa=False):
    # Frozen evaluator's mask is a transport tag here, not the source edit mask.
    # Source atom masks and arm names are kept in the immutable query manifest.
    values = [point['id'], '0' if qa else '1',
              ','.join(map(str, point['resources'])), ','.join(map(repr, point['keys']))]
    values.extend(','.join(map(str, point[k])) for k in FIELDS)
    values.append(','.join(map(repr, point['objectives'])) if qa else '')
    return '\t'.join(values)

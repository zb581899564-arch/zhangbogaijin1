"""Recheck original versus SHAM raw FE15000 fronts, without new evaluations."""
import json
from pathlib import Path
import sys


def checkpoint(path):
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    matches = [row for row in rows if row['checkpointKind'] == 'FE' and row['checkpoint'] == 15000]
    if len(matches) != 1:
        raise ValueError('Missing or duplicate FE15000 checkpoint')
    return matches[0]


def check(root, output):
    cells = []
    for original in (root / 'trials/demand').glob('*/*/SHARE_SPECIAL/anytime.jsonl'):
        sham = original.parent.parent / 'SHARE_SHAM_SPECIAL/anytime.jsonl'
        left, right = checkpoint(original), checkpoint(sham)
        if left['front'] != right['front'] or left['fe'] != right['fe'] or left['fe'] != 15000:
            raise ValueError('SHAM changed a raw fixed-FE front: ' + str(original))
        cells.append(str(original.relative_to(root)))
    if len(cells) != 30:
        raise ValueError('All30 complete original/SHAM pairs required')
    result = {'status': 'PASS', 'pairs': 30, 'checkpointFE': 15000,
              'rawFrontsExactlyEqual': True, 'extraFE': 0, 'cells': cells}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    check(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())

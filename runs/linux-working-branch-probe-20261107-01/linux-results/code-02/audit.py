"""Combine immutable identity, state replay and already-paid timeline verification."""
import importlib.util
from audit_inputs import loaded
from audit_search import verify
from common import *


def main(root):
    assert read(root/'prepared-independent-audit.json')['passed'] and read(root/'accounting.json')['passed']
    replay = verify(root)
    path = BASE/'runs/linux-counterfactual-edit-20261106-01/audit-code/audit.py'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('old_timeline', path)
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    operations = classes = count = 0; maximum = 0.; physical_values = {}
    qa = {s['id']: s for s in stream(root/'prepared/seeds.jsonl')}
    for kind in ('qa', 'science'):
        receipt = read(root/kind/'receipt.json'); classes += loaded(root, receipt['loaded'])
        seen = set()
        for number, row in enumerate(stream(root/kind/'evaluations.jsonl'), 1):
            assert row['number'] == number and row['id'] not in seen; seen.add(row['id'])
            if kind == 'qa':
                assert all(row[k] == qa[row['id']][k] for k in (*FIELDS, 'resources', 'keys', 'objectives'))
            n, error = old.timeline(row); operations += n; maximum = max(maximum, error); count += 1
            key = physical(row)
            if key in physical_values:
                assert physical_values[key] == row['objectives']
            physical_values[key] = row['objectives']
        if kind == 'qa':
            assert seen == set(qa)
    assert count == 1572 and operations == 314400
    result = dict(passed=True, rows=count, operationRecords=operations, maxAggregationError=maximum,
                  loadedClassChecks=classes, uniquePhysicalSchedules=len(physical_values),
                  timelineChecker=str(path), timelineCheckerSHA256=sha(path), stateReplay=replay, newDecoderCalls=0)
    write(root/'independent-audit.json', result)
    print('INDEPENDENT_AUDIT_PASSED', count, operations, flush=True)


if __name__ == '__main__':
    linux(); main(Path(sys.argv[1]))

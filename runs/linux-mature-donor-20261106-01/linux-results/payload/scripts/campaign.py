"""Single foreground campaign; no automatic expansion, tuning or background services."""
import argparse
import fcntl
from pathlib import Path
import platform
from protocol import freeze
from run_helpers import read, write, source_run, probe_run


def engineering(anchor, root, build, java, plan):
    reports = []
    for spec in plan['instances']:
        stem = spec['stem']; seed = plan['seeds'][0]
        records = {}
        for label, mode in [('NATIVE', 'NATIVE'), ('R_NATIVE', 'R_NATIVE'), ('R', 'R'), ('R_REPEAT', 'R'), ('G', 'G'), ('S', 'S'), ('UNION', 'UNION')]:
            out, receipt = probe_run(anchor, root, build, java, stem, seed, mode, label=label,
                                     engineering=True, import_qa=label == 'NATIVE')
            records[label] = (out, receipt)
        for a, b in [('NATIVE', 'R_NATIVE'), ('R', 'R_REPEAT')]:
            left, right = records[a], records[b]
            assert left[1]['paidSHA256'] == right[1]['paidSHA256'], (a, b, stem)
            assert read(left[0] / 'after.json') == read(right[0] / 'after.json')
            assert read(left[0] / 'front.json') == read(right[0] / 'front.json')
        before = read(records['R'][0] / 'before.json'); models = read(records['R'][0] / 'models.json')
        for out, receipt in records.values():
            assert read(out / 'before.json') == before and read(out / 'models.json') == models
        reference = (records['UNION'][0] / 'steps.jsonl').read_text().splitlines()
        for limit in [1, 2, plan['probeFE'][stem] - 1]:
            out, receipt = probe_run(anchor, root, build, java, stem, seed, 'UNION', label='CUT_' + str(limit), engineering=True, limit=limit)
            assert (out / 'steps.jsonl').read_text().splitlines() == reference[:limit]
        out, receipt = probe_run(anchor, root, build, java, stem, seed, 'UNION', label='FAIL_2', engineering=True, fail=True)
        assert (out / 'steps.jsonl').read_text().splitlines() == reference[:1]
        reports.append({'instance': stem, 'nativePaidParity': True, 'repeatParity': True, 'commonPModels': True,
                        'cutoffs': [1, 2, plan['probeFE'][stem] - 1], 'injectedFailure': receipt})
        print('DONOR_ENGINEERING_PASS', stem, flush=True)
    write(root / 'engineering-acceptance.json', {'passed': True, 'contexts': reports})


def fees(root):
    totals = {}
    for kind, glob in [('sources', 'sources/*/*/run-receipt.jsonl'), ('engineering', 'engineering/*/*/*/receipt.json'), ('science', 'science/*/*/*/receipt.json')]:
        values = [read(path) for path in root.glob(glob)]
        totals[kind] = {'runs': len(values), **{key: sum(row[key] for row in values) for key in ('attempted', 'successful', 'failed')},
                        'searchSeconds': sum(row['searchSeconds'] for row in values)}
    write(root / 'actual-fees.json', totals)
    return totals


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('anchor', 'root', 'build', 'java'): parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--action', choices=['first-capture', 'engineering', 'remaining-capture', 'science'], required=True)
    args = parser.parse_args(); root = args.root
    with (root / 'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        plan = freeze(args.anchor, root)
        if args.action.endswith('capture'):
            selected = plan['seeds'][:1] if args.action == 'first-capture' else plan['seeds'][1:]
            if args.action == 'remaining-capture': assert read(root / 'engineering-acceptance.json')['passed']
            for spec in plan['instances']:
                for seed in selected: source_run(args.anchor, root, args.build, args.java, spec['stem'], seed)
        elif args.action == 'engineering': engineering(args.anchor, root, args.build, args.java, plan)
        else:
            assert read(root / 'engineering-acceptance.json')['passed']
            for i, spec in enumerate(plan['instances']):
                stem = spec['stem']
                for j, seed in enumerate(plan['seeds']):
                    assert read(root / 'sources' / stem / str(seed) / 'equivalence.json')['passed']
                    order = plan['arms']; shift = (i+j) % len(order)
                    for mode in order[shift:] + order[:shift]:
                        probe_run(args.anchor, root, args.build, args.java, stem, seed, mode, import_qa=mode == 'R' and j > 0)
                    print('DONOR_SCIENCE_CONTEXT', stem, seed, flush=True)
            totals = fees(root)
            assert totals['science']['successful'] == 284160 and totals['science']['failed'] == 0
            assert totals['engineering']['attempted'] == plan['engineeringAttemptedFE']
            assert sum(r['attempted'] for r in totals.values()) == plan['totalPlannedAttemptedFE']
            write(root / 'science-complete.json', {'passed': True, 'fees': totals, 'statisticsPending': True})
        print('ACTION_COMPLETE', args.action, flush=True)


if __name__ == '__main__': main()

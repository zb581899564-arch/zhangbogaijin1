"""Foreground Linux three-arm campaign with explicit engineering admission."""
import argparse
import fcntl
import os
from pathlib import Path
import platform
import subprocess
import time
from urllib.parse import urlparse, unquote
from prepare import read, write, sha


def load():
    return dict(epoch=time.time(), load=os.getloadavg(), memory=Path('/proc/meminfo').read_text(),
                processes=subprocess.check_output(['ps', '-eo', 'pid,user,pcpu,pmem,comm', '--sort=-pcpu'], text=True).splitlines()[:14])


def run_one(args, stem, seed, mode, label=None, engineering=False, native=False, limit=None, fail=False, imports=False):
    out = args.root / ('engineering' if engineering else 'science') / stem / str(seed) / (label or mode)
    out.mkdir(parents=True, exist_ok=False)
    inputs = args.anchor / 'payload/inputs' / stem
    flags = ['-Dresearch.pilot.physics=' + str(engineering).lower(),
             '-Dresearch.postlocal.importQA=' + str(imports).lower(),
             '-Dresearch.postlocal.nativeObserver=' + str(native).lower()]
    if limit is not None: flags.append('-Dresearch.postlocal.limit=' + str(limit))
    if fail: flags.append('-Dresearch.pilot.failAt=2')
    command = ['nice', '-n', '10', str(args.java), *flags, '-cp', (args.build / 'classpath.txt').read_text().strip(),
               'research.dynamic.PostLocalProbeRun', str(inputs / (stem + '.txt')), str(inputs / 'RECONSTRUCTED-setup.txt'),
               str(inputs / 'fatigue-input.txt'), str(out), str(args.root / 'inputs' / stem / str(seed)), mode, str(seed)]
    write(out / 'command.json', command); write(out / 'load-before.json', load())
    start = time.perf_counter()
    with (out / 'run.log').open('x') as stream:
        process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    write(out / 'process.json', dict(exitCode=process.returncode, seconds=time.perf_counter() - start))
    write(out / 'load-after.json', load())
    assert (process.returncode != 0) == fail, str(out)
    receipt = read(out / 'receipt.json')
    expected = limit if limit is not None else receipt['expectedFE']
    if fail: assert (receipt['attempted'], receipt['successful'], receipt['failed']) == (2, 1, 1)
    else: assert receipt['attempted'] == receipt['successful'] == expected and receipt['failed'] == 0
    assert receipt['decoder']['dynamic.evaluations'] == receipt['successful']
    if engineering: assert receipt['physicsQA']['fullTimelineChecks'] == receipt['successful']
    for name, identity in receipt['loaded'].items():
        if isinstance(identity, dict):
            resource = identity['resource']
            if resource.startswith('file:'):
                assert sha(Path(unquote(urlparse(resource).path))) == identity['sha256'], name
    print('POSTLOCAL_RUN', stem, seed, label or mode, receipt['successful'], flush=True)
    return out, receipt


def engineering(args, plan):
    contexts = []
    for stem in plan['instances']:
        seed, budget = plan['seeds'][0], plan['passFE'][stem]
        records = {}
        for label in ['RAW_NATIVE', 'RAW_ROLE', 'POST_ROLE', 'POST_PARETO']:
            mode = 'RAW_ROLE' if label == 'RAW_NATIVE' else label
            records[label] = run_one(args, stem, seed, mode, label, True,
                                     native=label == 'RAW_NATIVE', imports=label == 'RAW_NATIVE')
        assert records['RAW_NATIVE'][1]['paidSHA256'] == records['RAW_ROLE'][1]['paidSHA256']
        for name in ['front.json', 'after.json']:
            assert read(records['RAW_NATIVE'][0] / name) == read(records['RAW_ROLE'][0] / name)
        assert records['POST_ROLE'][1]['prefix2BSHA256'] == records['POST_PARETO'][1]['prefix2BSHA256']
        for limit in [1, 2, budget, 2 * budget, 3 * budget - 1]:
            run_one(args, stem, seed, 'POST_ROLE', 'CUT_' + str(limit), True, limit=limit)
        run_one(args, stem, seed, 'POST_ROLE', 'FAIL_2', True, fail=True)
        contexts.append(dict(instance=stem, nativeObserverParity=True, postPrefixParity=True,
                             cutoffs=[1, 2, budget, 2 * budget, 3 * budget - 1]))
    write(args.root / 'engineering-runtime-acceptance.json', dict(passed=True, contexts=contexts, independentAuditPending=True))


def fees(root):
    totals = {}
    for kind in ['engineering', 'science']:
        receipts = [read(p) for p in (root / kind).glob('*/*/*/receipt.json')]
        totals[kind] = dict(runs=len(receipts), **{k: sum(r[k] for r in receipts)
                           for k in ['attempted', 'successful', 'failed', 'searchSeconds']})
    return totals


def science(args, plan):
    assert read(args.root / 'engineering-runtime-acceptance.json')['passed']
    assert read(args.root / 'engineering-independent-audit.json')['passed']
    for i, stem in enumerate(plan['instances']):
        for j, seed in enumerate(plan['seeds']):
            order = plan['arms']; shift = (i + j) % len(order)
            for mode in order[shift:] + order[:shift]:
                out, receipt = run_one(args, stem, seed, mode, imports=mode == 'RAW_ROLE' and j > 0)
                if j == 0:
                    prior = read(args.root / 'engineering' / stem / str(seed) / mode / 'receipt.json')
                    assert prior['paidSHA256'] == receipt['paidSHA256'], 'Physics QA changed search'
    totals = fees(args.root)
    assert totals['science']['successful'] == plan['scienceFE'] and totals['science']['failed'] == 0
    assert totals['engineering']['attempted'] == plan['engineeringAttemptedFE']
    write(args.root / 'actual-fees.json', totals)
    write(args.root / 'science-complete.json', dict(passed=True, fees=totals, statisticsPending=True))


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['root', 'anchor', 'build', 'java']:
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--action', choices=['engineering', 'science'], required=True)
    args = parser.parse_args(); plan = read(args.root / 'protocol.json')
    assert read(args.root / 'source-acceptance.json')['passed']
    with (args.root / 'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (engineering if args.action == 'engineering' else science)(args, plan)


if __name__ == '__main__':
    main()

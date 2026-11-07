"""Foreground Linux pilot: engineering first, then one fixed 18-run scientific batch."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import platform
import subprocess
import sys

from protocol import freeze
from run_support import read, write, initial, run_case, accounting, verify_artifacts, sha
from engineering import engineering, lifecycle


def main(args):
    if platform.system() != 'Linux' or sys.version_info[:2] != (3, 11):
        raise RuntimeError('Linux Python3.11 required')
    payload, out, build = args.payload.resolve(), args.output.resolve(), args.build.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out/'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_artifacts(payload)
        plan = freeze(payload, out)
        if args.action == 'engineering':
            assert not (out/'engineering').exists(), 'Retain prior attempt; do not overwrite'
            env = {'python': sys.version, 'platform': platform.platform(), 'hostname': platform.node(),
                   'java': subprocess.run([str(args.java), '-version'], capture_output=True, text=True, check=True).stderr,
                   'dependencies': subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True).stdout,
                   'buildClassIdentity': read(build/'class-identities.json'),
                   'inputHashes': {str(p.relative_to(payload)): sha(p) for p in (payload/'inputs').rglob('*') if p.is_file()}}
            write(out/'environment.json', env)
            engineering(payload, build, args.java, out/'engineering', plan)
        elif args.action == 'science':
            assert read(out/'engineering/acceptance.json')['passed']
            assert read(out/'math-checks.json')['passed']
            assert read(out/'environment.json')['buildClassIdentity'] == read(build/'class-identities.json')
            assert not (out/'science').exists(), 'No implicit restart or overwriting'
            for i, spec in enumerate(plan['instances']):
                for k, seed in enumerate(plan['seeds']):
                    shift=(i+k)%3
                    order=plan['arms'][shift:]+plan['arms'][:shift]
                    common=None
                    for arm in order:
                        dest=out/'science'/spec['stem']/str(seed)/arm
                        receipt=run_case(payload, build, args.java, dest, spec['stem'], seed, arm, plan['fePerRun'])
                        current=initial(dest)
                        if common is None: common=current
                        assert len(current)==100 and current==common
                        assert lifecycle(dest, arm, receipt)>0
            fees=accounting(out/'science')
            assert fees==dict(attempted=9000000, successful=9000000, failed=0), fees
            write(out/'science-complete.json', {'passed': True, 'fees': fees, 'runs': 18, 'statisticsPending': True})
        else:
            raise ValueError(args.action)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--action', choices=['engineering', 'science'], required=True)
    main(parser.parse_args())
